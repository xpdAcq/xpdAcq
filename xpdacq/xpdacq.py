import os
import uuid
import time
import yaml
from itertools import count

import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.suspenders import SuspendFloor

from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .beamtime import *

from xpdan.tools import compress_mask


def _summarize(plan):
    """based on bluesky.utils.print_summary"""
    output = []
    read_cache = []
    for msg in plan:
        cmd = msg.command
        if cmd == 'open_run':
            output.append('{:=^80}'.format(' Open Run '))
        elif cmd == 'close_run':
            output.append('{:=^80}'.format(' Close Run '))
        elif cmd == 'set':
            output.append('{motor.name} -> {args[0]}'.format(motor=msg.obj,
                                                             args=msg.args))
        elif cmd == 'create':
            pass
        elif cmd == 'read':
            read_cache.append(msg.obj.name)
        elif cmd == 'save':
            output.append('  Read {}'.format(read_cache))
            read_cache = []
    return '\n'.join(output)


def _update_dark_dict_list(name, doc):
    """ generate dark frame reference

    This function should be subscribed to 'stop' documents from dark
    frame runs.
    """
    # always grab from glbl state 
    dark_dict_list = list(glbl._dark_dict_list)
    # obtain light count time that is already set to glbl.pe1c
    acq_time = glbl.area_det.cam.acquire_time.get()
    num_frame = glbl.area_det.images_per_set.get()
    light_cnt_time = acq_time * num_frame

    dark_dict = {}
    dark_dict['acq_time'] = acq_time
    dark_dict['exposure'] = light_cnt_time
    dark_dict['timestamp'] = doc['time']
    dark_dict['uid'] = doc['run_start']
    dark_dict_list.append(dark_dict)
    glbl._dark_dict_list = dark_dict_list  # update glbl._dark_dict_list


def take_dark():
    """a plan for taking a single dark frame"""
    print('INFO: closing shutter...')
    # 60 means open at XPD, Oct.4, 2016
    yield from bp.abs_set(glbl.shutter, 0, wait=True)
    #if glbl.shutter_control:
    #    yield from bp.sleep(2)
    print('INFO: taking dark frame....')
    # upto this stage, glbl.pe1c has been configured to so exposure time is
    # correct
    acq_time = glbl.area_det.cam.acquire_time.get()
    num_frame = glbl.area_det.images_per_set.get()
    computed_exposure = acq_time * num_frame
    # update md
    _md = {'sp_time_per_frame': acq_time,
           'sp_num_frames': num_frame,
           'sp_computed_exposure': computed_exposure,
           'sp_type': 'ct',
           # 'sp_uid': str(uuid.uuid4()), # dark plan doesn't need uid
           'sp_plan_name': 'dark_{}'.format(computed_exposure),
           'dark_frame': True}
    c = bp.count([glbl.area_det], md=_md)
    yield from bp.subs_wrapper(c, {'stop': [_update_dark_dict_list]})
    print('opening shutter...')
    # 60 means open at XPD, Oct.4, 2016
    #yield from bp.abs_set(glbl.shutter, 60, wait=True)
    #if glbl.shutter_control:
    #    yield from bp.sleep(2)


def periodic_dark(plan):
    """
    a plan wrapper that takes a plan and inserts `take_dark`

    The `take_dark` plan is inserted on the fly before the beginning of
    any new run after a period of time defined by `glbl.dk_window` has passed.
    """
    need_dark = True

    def insert_take_dark(msg):
        now = time.time()
        nonlocal need_dark
        qualified_dark_uid = _validate_dark(expire_time=glbl.dk_window)
        # FIXME: should we do "or" or "and"?
        if (not need_dark) and (not qualified_dark_uid):
            need_dark = True
        if need_dark \
                and (not qualified_dark_uid) \
                and msg.command == 'open_run' \
                and ('dark_frame' not in msg.kwargs):
            # We are about to start a new 'run' (e.g., a count or a scan).
            # Insert a dark frame run first.
            need_dark = False
            # Annoying detail: the detector was probably already staged.
            # Unstage it (if it wasn't staged, nothing will happen) and
            # then take_dark() and then re-stage it. 
            return bp.pchain(bp.unstage(glbl.area_det),
                             take_dark(),
                             bp.stage(glbl.area_det),
                             bp.single_gen(msg),
                             bp.abs_set(glbl.shutter, 60, wait=True)), None
        elif msg.command == 'open_run' and 'dark_frame' not in msg.kwargs:
            return bp.pchain(bp.single_gen(msg),
                             bp.abs_set(glbl.shutter, 60, wait=True)), None
        else:
            # do nothing if (not need_dark)
            return None, None

    return (yield from bp.plan_mutator(plan, insert_take_dark))


def _validate_dark(expire_time=None):
    """ find appropriate dark frame uid stored in dark_dict_list

    element in dark_scan_dict is expected to be a dict with following
    keys: 'exposure', 'uid' and 'timestamp'

    """
    if expire_time is None:
        expire_time = glbl.dk_window
    dark_dict_list = glbl._dark_dict_list
    # if glbl.dark_dict_list = None, do a dark anyway
    if not dark_dict_list:
        return None
    # obtain light count time that is already set to pe1c
    acq_time = glbl.area_det.cam.acquire_time.get()
    num_frame = glbl.area_det.images_per_set.get()
    light_cnt_time = acq_time * num_frame
    # find fresh and qualified dark
    now = time.time()
    qualified_dark_uid = [el['uid'] for el in dark_dict_list if
                          abs(el['exposure'] - light_cnt_time) <= acq_time
                          and abs(el['timestamp'] - now)
                          <= (expire_time * 60 - acq_time)
                          and (el['acq_time'] == acq_time)
                          ]
    if qualified_dark_uid:
        return qualified_dark_uid[-1]
    else:
        return None


def _auto_load_calibration_file():
    """ function to load the most recent calibration file in config_base

    Returns
    -------
    config_md_dict : dict
    dictionary contains calibration parameters computed by pyFAI
    and file name of the most recent calibration. If no calibration
    file exits in xpdUser/config_base, returns None.
    """

    config_dir = glbl.config_base
    if not os.path.isdir(config_dir):
        raise RuntimeError("WARNING: Required directory {} doesn't"
                           " exist, did you accidentally delete it?"
                           .format(glbl.config_base))
    calib_yaml_name = os.path.join(glbl.config_base,
                                   glbl.calib_config_name)
    if not os.path.isfile(calib_yaml_name):
        print("INFO: No calibration file found in config_base. "
              "Scan will still keep going on")
        return
    config_dict = getattr(glbl, 'calib_config_dict', None)
    # prviate test: equality
    with open(calib_yaml_name) as f:
        yaml_reload_dict = yaml.load(f)
    if config_dict != yaml_reload_dict:
        config_dict = yaml_reload_dict
    # trust file-based dict, in case user change attribute
    print("INFO: This scan will append calibration parameters "
          "recorded in {}".format(config_dict['file_name']))
    return config_dict


def _inject_qualified_dark_frame_uid(msg):
    if msg.command == 'open_run' and msg.kwargs.get('dark_frame') != True:
        dark_uid = _validate_dark(glbl.dk_window)
        msg.kwargs['sc_dk_field_uid'] = dark_uid
    return msg


def _inject_calibration_md(msg):
    if msg.command == 'open_run':
        # it user has run a calibration set before
        calibration_md = _auto_load_calibration_file()
        if calibration_md:
            injected_calib_dict = dict(calibration_md)
            injected_calib_uid = injected_calib_dict.pop(
                                 'calibration_collection_uid')
            msg.kwargs['calibration_md'] = injected_calib_dict
            msg.kwargs['calibration_collection_uid'] = injected_calib_uid
    return msg


def _inject_mask(msg):
    if msg.command == 'open_run':
        mask = getattr(glbl, 'mask', None)
        if mask is not None:
            print("INFO: insert mask into your header")
            data, indicies, indptr = compress_mask(mask)  # rv are lists
            msg.kwargs['mask'] = (data, indicies,
                                  indptr)
        else:
            print("INFO: no mask has been associated with current glbl")

    return msg

def open_collection(collection_name):
    """ function to open a collection of your following scans

    collection is a list of uid of executed scans. 
    Only one collection will be alive in collection environment. 
    This set of uids will be saved as a yaml file and desired operations 
    can be applied later.

    Parameters
    ----------
    collection_name : str
        name of your collection, suggested to have discernible name
    """

    print("INFO: open collection")
    glbl._cnt = count()
    glbl.collection_num = next(glbl._cnt)
    glbl._collection_ref_num = 0
    # get current object
    collection = getattr(glbl, 'collection', None)
    if collection is None:
        glbl.collection = []
    collection = list(glbl.collection)
    # save current object
    current_name = getattr(glbl, 'collection_name', None)
    if current_name is not None:
        with open(os.path.join(glbl.usrAnalysis_dir, current_name) + '.yaml',
                  'w') as f:
            yaml.dump(collection, f)
    # create new name
    new_name = '_'.join([collection_name, str(uuid.uuid4())[:5]])
    glbl.collection_name = new_name
    # update collection
    glbl.collection = []


def _insert_collection(collection_name, collection_obj, new_uid=None):
    print('Update collection')
    collection_obj.extend(new_uid)
    new_num = next(glbl._cnt)
    ref_num = glbl._collection_ref_num
    glbl.collection_num = new_num
    if new_num - ref_num >= 5:
        # print("yamlize obj, ref_num = {}, new_num = {}"
        #      .format(ref_num, new_num))
        glbl._collection_ref_num = new_num
        with open(os.path.join(glbl.usrAnalysis_dir,
                               collection_name) + '.yaml', 'w') as f:
            yaml.dump(glbl.collection, f)


class CustomizedRunEngine(RunEngine):
    def __init__(self, beamtime, *args, **kwargs):
        """ A RunEngine customized for XPD workflows.

        Parameters
        ----------
        beamtime : xpdacq.beamtime.Beamtime or None
            current beamtime object

        Examples
        --------
        Basic usage...

        Run samples and plans by number...
        >>> xrun(0, 0)

        Advanced usage...

        Use custom plans
        >>> xrun(3, custom_plan)  # sample 3, an arbitrary bluesky plan

        Or custom sample info --- sample just has to be dict-like
        and contain the required keys.
        >>> xrun(custom_sample_dict, custom_plan)

        Or use completely custom dark frame logic
        >>> xrun(3, 'ct', dark_strategy=some_custom_func)
        """
        super().__init__(*args, **kwargs)
        self._beamtime = beamtime

    @property
    def beamtime(self):
        if self._beamtime is None:
            raise RuntimeError("Your beamtime environment is not properly "
                               "setup. Please do\n"
                               ">>> xrun.beamtime = bt\n"
                               "then retry")
        return self._beamtime

    @beamtime.setter
    def beamtime(self, bt_obj):
        self._beamtime = bt_obj
        self.md.update(bt_obj.md)
        print("INFO: beamtime object has been linked\n")
        # from xpdacq.calib import run_calibration
        if not glbl._is_simulation:
            self.subscribe('all', glbl.db.mds.insert)
            # let user deal with suspender
            #beamdump_sus = SuspendFloor(glbl.ring_current, 50,
            #                            resume_thresh=glbl.ring_current.get() * 0.9,
            #                            sleep=1200)
            #glbl.suspender = beamdump_sus
            # FIXME : print info for user
            # self.install_suspender(beamdump_sus)
            # print("INFO: beam dump suspender has been created."
            #        " to check, please do\n:"
            #        ">>> xrun.suspenders")
        else:
            pass

    def __call__(self, sample, plan, subs=None, *,
                 verify_write=False, dark_strategy=periodic_dark,
                 raise_if_interrupted=False, **metadata_kw):
        # The CustomizedRunEngine knows about a Beamtime object, and it
        # interprets integers for 'sample' as indexes into the Beamtime's
        # lists of Samples from all its Experiments.

        # deprecated from v0.5 release
        #if getattr(glbl, 'collection', None) is None:
        #    raise RuntimeError("No collection has been linked to current "
        #                       "experiment yet.\nPlease do\n"
        #                       ">>> open_collection(<collection_name>)\n"
        #                       "before you run any xrun")

        if isinstance(sample, int):
            try:
                sample = self.beamtime.samples[sample]
            except IndexError:
                print("WARNING: hmm, there is no sample with index `{}`"
                      ", please do `bt.list()` to check if it exists yet"
                      .format(sample))
                return
        # If a plan is given as a string, look in up in the global registry.
        if isinstance(plan, int):
            try:
                plan = self.beamtime.scanplans[plan]
            except IndexError:
                print("WARNING: hmm, there is no scanplan with index `{}`"
                      ", please do `bt.list()` to check if it exists yet"
                      .format(plan))
                return
        # If the plan is an xpdAcq 'ScanPlan', make the actual plan.
        if isinstance(plan, ScanPlan):
            plan = plan.factory()
        _subs = normalize_subs_input(subs)
        if verify_write:
            _subs.update({'stop': verify_files_saved})
        # No keys in metadata_kw are allows to collide with sample keys.
        if set(sample) & set(metadata_kw):
            raise ValueError("These keys in metadata_kw are illegal "
                             "because they are always in sample: "
                             "{}".format(set(sample) & set(metadata_kw)))
        if self._beamtime.get('bt_wavelength') is None:
            print("WARNING: there is no wavelength information in current"
                  "beamtime object, scan will keep going....")
        metadata_kw.update(sample)
        sh = glbl.shutter

        if glbl.shutter_control:
            # Alter the plan to incorporate dark frames.
            # only works if user allows shutter control
            if glbl.auto_dark:
                plan = dark_strategy(plan)
                plan = bp.msg_mutator(plan, _inject_qualified_dark_frame_uid)
            # force to close shutter after scan
            plan = bp.finalize_wrapper(plan, bp.abs_set(sh, 0, wait=True))

        # Load calibration file
        if glbl.auto_load_calib:
            plan = bp.msg_mutator(plan, _inject_calibration_md)

        # Insert glbl mask
        plan = bp.msg_mutator(plan, _inject_mask)

        # Execute
        return super().__call__(plan, subs,
                                raise_if_interrupted=raise_if_interrupted,
                                **metadata_kw)

        # deprecated from v0.5 release
        # insert collection
        #_insert_collection(glbl.collection_name, glbl.collection,
        #                   self._run_start_uids)
