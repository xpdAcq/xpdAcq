import os
import uuid
import time
import yaml
import inspect
import datetime
from collections import ChainMap
from configparser import ConfigParser

import numpy as np
import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.callbacks import LiveTable

# FIXME use exact import after entire cleaning
from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .validated_dict import ValidatedDictLike
from .beamtimeSetup import start_xpdacq
from .beamtime import *

def _summarize(plan):
    "based on bluesky.utils.print_summary"
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
    glbl._dark_dict_list = dark_dict_list # update glbl._dark_dict_list


def take_dark():
    "a plan for taking a single dark frame"
    print('INFO: closing shutter...')
    yield from bp.abs_set(glbl.shutter, 0)
    if glbl.shutter_control:
        yield from bp.sleep(2)
    print('INFO: taking dark frame....')
    # upto this stage, glbl.pe1c has been configured to so exposure time is
    # correct
    c = bp.count([glbl.area_det], md={'dark_frame': True})
    yield from bp.subs_wrapper(c, {'stop': [_update_dark_dict_list]})
    print('opening shutter...')
    yield from bp.abs_set(glbl.shutter, 1)
    if glbl.shutter_control:
        yield from bp.sleep(2)


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
        if ((not need_dark) and (not qualified_dark_uid)):
            need_dark = True
        if need_dark and msg.command == 'open_run' and ('dark_frame' not
                                                         in msg.kwargs):
            # We are about to start a new 'run' (e.g., a count or a scan).
            # Insert a dark frame run first.
            need_dark = False
            # Annoying detail: the detector was probably already staged.
            # Unstage it (if it wasn't staged, nothing will happen) and
            # then take_dark() and then re-stage it. 
            return bp.pchain(bp.unstage(glbl.area_det),
                             take_dark(),
                             bp.stage(glbl.area_det),
                             bp.single_gen(msg)), None
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
    qualified_dark_uid = [ el['uid'] for el in dark_dict_list if
                         abs(el['exposure'] - light_cnt_time) <= acq_time and
                         abs(el['timestamp'] - now) <= (expire_time*60 - acq_time)
                         and (el['acq_time'] == acq_time)
                         ]
    if qualified_dark_uid:
        return qualified_dark_uid[-1]
    else :
        return None


def _timestamp_to_time(timestamp):
    """ short help function """
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d-%H%M')


def _auto_load_calibration_file():
    """ function to load the most recent calibration file in config_base

    Returns
    -------
    config_md_dict : dict
    dictionary contains calibration parameters computed by SrXplanar,
    file name and timestamp of the most recent calibration file.
    If no calibration file exits in xpdUser/config_base, returns None.
    """

    config_dir = glbl.config_base
    if not os.path.isdir(config_dir):
        raise RuntimeError("WARNING: Required directory {} doesn't"
                           " exist, did you accidentally delete it?"
                           .format(glbl.config_base))
    f_list = [ f for f in os.listdir(config_dir) if f.endswith('cfg')]
    if not f_list:
        print("INFO: No calibration file found in config_base."
              "Scan will still keep going on")
        return
    f_list_full_path = list(map(lambda f: os.path.join(config_dir, f), f_list))
    sorted_list = sorted(f_list_full_path, key=os.path.getmtime)
    config_in_use = sorted_list [-1]
    print("INFO: This scan will append calibration parameters recorded"
          " in {}".format(os.path.basename(config_in_use)))
    config_timestamp = os.path.getmtime(config_in_use)
    config_time = _timestamp_to_time(config_timestamp)
    config_dict = _parse_calibration_file(os.path.join(config_dir,
                                                       config_in_use))
    # FIXME - finalized format?
    config_md_dict = {'parameters':config_dict,
                      'file_name': os.path.basename(config_in_use),
                      'timestamp':config_time}
    return config_md_dict


def _parse_calibration_file(config_file_name):
    ''' helper function to parse calibration file '''
    calibration_parser = ConfigParser()
    calibration_parser.read(config_file_name)
    sections = calibration_parser.sections()
    config_dict = {}
    for section in sections:
        config_dict[section] = {} # write down header
        options = calibration_parser.options(section)
        for option in options:
            try:
                config_dict[section][option] = calibration_parser.get(section,
                                                                      option)
                # if config_dict[option] == -1:
                # DebugPrint("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                config_dict[option] = None
    return config_dict


def _inject_qualified_dark_frame_uid(msg):
    if msg.command == 'open_run' and msg.kwargs.get('dark_frame') != True:
        dark_uid = _validate_dark(glbl.dk_window)
        msg.kwargs['dark_frame_uid'] = dark_uid
    return msg


def _inject_calibration_md(msg):
    if msg.command == 'open_run':
        calibration_md = _auto_load_calibration_file()
        msg.kwargs['calibration_md'] = calibration_md
    return msg


class CustomizedRunEngine(RunEngine):
    def __init__(self, beamtime, *args, **kwargs):
        """
        A RunEngine customized for XPD workflows.

        Parameters
        ----------
        beamtime : Beamtime

        Examples
        --------
        Automatic configuration during startup process...
        >>> bt = load_beamtime('some/directory/pi_name')
        >>> prun = CustomizedRunEngine(bt)

        Basic usage...

        Inspect avaiable experiments, samples, plans.
        >>> print(bt)
        Experiments:
        0: another_test

        ScanPlans:
        0: (...summary of scanplan...)

        Samples:
        0: name

        Run samples and plans by number...
        >>> prun(0, 0)

        ... or by name.
        >>> prun(3, 'ct')  # Do an XPD count ('ct') plan on Sample 3.

        Advanced usage...

        Use custom plans
        >>> prun(3, custom_plan)  # sample 3, an arbitrary bluesky plan

        Or custom sample info --- sample just has to be dict-like
        and contain the required keys.
        >>> prun(custom_sample_dict, custom_plan)

        Customize dark frame period
        >>> prun(3, 'ct', dark_strategy=partial(periodic_dark, period=1000)

        Or use completely custom dark frame logic
        >>> prun(3, 'ct', dark_strategy=some_custom_func)
        """
        super().__init__(*args, **kwargs)
        self.beamtime = beamtime

    def __call__(self, sample, plan, subs=None, *,
                 verify_write=False, dark_strategy=periodic_dark,
                 raise_if_interrupted=False, **metadata_kw):
        # The CustomizedRunEngine knows about a Beamtime object, and it
        # interprets integers for 'sample' as indexes into the Beamtime's
        # lists of Samples from all its Experiments.
        if isinstance(sample, int):
            sample = self.beamtime.samples[sample]
        # If a plan is given as a string, look in up in the global registry.
        if isinstance(plan, str):
            # e.g., 'ct'
            plan = _PLAN_REGISTRY[plan]
        elif isinstance(plan, int):
            plan = self.beamtime.scanplans[plan]
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
        metadata_kw.update(sample)
        sh = glbl.shutter
        # force to open shutter before scan and close it after
        plan = bp.pchain(bp.abs_set(sh, 1), plan, bp.abs_set(sh, 0))
        # Alter the plan to incorporate dark frames.
        if glbl.auto_dark:
            plan = dark_strategy(plan)
            plan = bp.msg_mutator(plan, _inject_qualified_dark_frame_uid)
        # Load calibration file
        plan = bp.msg_mutator(plan, _inject_calibration_md)
        # Execute
        super().__call__(plan, subs,
                         raise_if_interrupted=raise_if_interrupted,
                         **metadata_kw)

        return self._run_start_uids

# load beamtime
bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload and hook beamtime objects:\n{}".format(bt))
    prun = CustomizedRunEngine(bt)
