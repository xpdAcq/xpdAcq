#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Dan Allan, Thomas A. Caswell
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import uuid
import time
import yaml
import warnings
import numpy as np

import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.suspenders import SuspendFloor
from bluesky.utils import normalize_subs_input

from xpdacq.glbl import glbl
from xpdacq.xpdacq_conf import (xpd_configuration, XPD_SHUTTER_CONF,
                                XPDACQ_MD_VERSION)
from xpdacq.beamtime import ScanPlan, _summarize

from xpdan.tools import compress_mask

XPD_shutter = xpd_configuration.get('shutter')


def _update_dark_dict_list(name, doc):
    """ generate dark frame reference

    This function should be subscribed to 'stop' documents from dark
    frame runs.
    """
    # always grab from glbl state
    dark_dict_list = list(glbl['_dark_dict_list'])
    # obtain light count time that is already set to area_det
    area_det = xpd_configuration['area_det']
    acq_time = area_det.cam.acquire_time.get()
    num_frame = area_det.images_per_set.get()
    light_cnt_time = acq_time * num_frame

    dark_dict = {}
    dark_dict['acq_time'] = acq_time
    dark_dict['exposure'] = light_cnt_time
    dark_dict['timestamp'] = doc['time']
    dark_dict['uid'] = doc['run_start']
    if doc['exit_status'] == 'success':
        print('dark frame complete, update dark dict')
        dark_dict_list.append(dark_dict)
        glbl['_dark_dict_list'] = dark_dict_list  # update glbl._dark_dict_list
    else:
        #FIXME: replace with logging and detailed warning next PR
        print("INFO: dark scan was not successfully executed.\n"
              "gobal dark frame information will not be updated!")


def take_dark():
    """a plan for taking a single dark frame"""
    print('INFO: closing shutter...')
    yield from bp.abs_set(xpd_configuration.get('shutter'),
                          XPD_SHUTTER_CONF['close'],
                          wait=True)
    print('INFO: taking dark frame....')
    # upto this stage, area_det has been configured to so exposure time is
    # correct
    area_det = xpd_configuration['area_det']
    acq_time = area_det.cam.acquire_time.get()
    num_frame = area_det.images_per_set.get()
    computed_exposure = acq_time * num_frame
    # update md
    _md = {'sp_time_per_frame': acq_time,
           'sp_num_frames': num_frame,
           'sp_computed_exposure': computed_exposure,
           'sp_type': 'ct',
           'sp_plan_name': 'dark_{}'.format(computed_exposure),
           'dark_frame': True}
    c = bp.count([area_det], md=_md)
    yield from bp.subs_wrapper(c, {'stop': [_update_dark_dict_list]})
    print('opening shutter...')


def periodic_dark(plan):
    """
    a plan wrapper that takes a plan and inserts `take_dark`

    The `take_dark` plan is inserted on the fly before the beginning of
    any new run after a period of time defined by glbl['dk_window'] has passed.
    """
    need_dark = True

    def insert_take_dark(msg):
        now = time.time()
        nonlocal need_dark
        qualified_dark_uid = _validate_dark(expire_time=glbl['dk_window'])
        area_det = xpd_configuration['area_det']

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
            return bp.pchain(bp.unstage(area_det),
                             take_dark(),
                             bp.stage(area_det),
                             bp.single_gen(msg),
                             bp.abs_set(xpd_configuration.get('shutter'),
                                        XPD_SHUTTER_CONF['open'],
                                        wait=True)
                             ), None
        elif msg.command == 'open_run' and 'dark_frame' not in msg.kwargs:
            return bp.pchain(bp.single_gen(msg),
                             bp.abs_set(xpd_configuration.get('shutter'),
                                        XPD_SHUTTER_CONF['open'],
                                        wait=True)
                             ), None
        else:
            # do nothing if (not need_dark)
            return None, None

    return (yield from bp.plan_mutator(plan, insert_take_dark))


def _validate_dark(expire_time=None):
    """find appropriate dark frame uid stored in dark_dict_list

    element in dark_scan_dict is expected to be a dict with following
    keys: 'exposure', 'uid' and 'timestamp'
    """
    if expire_time is None:
        expire_time = glbl['dk_window']
    dark_dict_list = glbl['_dark_dict_list']
    # if glbl.dark_dict_list = None, do a dark anyway
    if not dark_dict_list:
        return None
    # obtain light count time that is already set to pe1c
    area_det = xpd_configuration['area_det']
    acq_time = area_det.cam.acquire_time.get()
    num_frame = area_det.images_per_set.get()
    light_cnt_time = acq_time * num_frame
    # find fresh and qualified dark
    now = time.time()
    qualified_dark_list = []
    for el in dark_dict_list:
        expo_diff = abs(el['exposure'] - light_cnt_time)
        time_diff = abs(el['timestamp'] - now)
        if (expo_diff < acq_time) and \
                (time_diff < expire_time * 60) and \
                (el['acq_time'] == acq_time):
            qualified_dark_list.append((el.get('uid'), expo_diff,
                                        time_diff))
    if qualified_dark_list:
        # sort wrt expo_diff and time_diff for best candidate
        #best_dark = sorted(qualified_dark_list,
        #                   key=lambda x: x[1] and x[2])[0]
        best_dark = sorted(qualified_dark_list,
                           key=lambda x: x[2])[0]
        best_dark_uid = best_dark[0]
        return best_dark_uid
    else:
        return None


def _auto_load_calibration_file():
    """function to load the most recent calibration file in config_base

    Returns
    -------
    config_md_dict : dict
    dictionary contains calibration parameters computed by pyFAI
    and file name of the most recent calibration. If no calibration
    file exits in xpdUser/config_base, returns None.
    """

    config_dir = glbl['config_base']
    if not os.path.isdir(config_dir):
        raise RuntimeError("WARNING: Required directory {} doesn't"
                           " exist, did you accidentally delete it?"
                           .format(config_dir))
    calib_yaml_name = os.path.join(config_dir,
                                   glbl['calib_config_name'])
    if not os.path.isfile(calib_yaml_name):
        print("INFO: No calibration file found in config_base.\n"
              "Scan will still keep going on....")
        return
    config_dict = glbl.get('calib_config_dict', None)
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
    if msg.command == 'open_run' and msg.kwargs.get('dark_frame') is not True:
        dark_uid = _validate_dark(glbl['dk_window'])
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


def _inject_xpdacq_md_version(msg):
    """simply insert xpdAcq md version"""
    if msg.command == 'open_run':
        msg.kwargs['xpdacq_md_version'] = XPDACQ_MD_VERSION
    return msg


def _inject_mask(msg):
    if msg.command == 'open_run':
        mask_path = glbl['mask_path']
        if os.path.isfile(mask_path):
            mask = np.load(mask_path)
            print("INFO: insert mask into your header")
            data, indicies, indptr = compress_mask(mask)  # rv are lists
            msg.kwargs['mask'] = (data, indicies,
                                  indptr)
        else:
            print("INFO: no mask has been built, scan will keep going...")

    return msg


def _inject_mask_server_uid(msg):
    if msg.command == 'open_run':
        mask_server_uid = glbl.get('mask_server_uid', None)
        if mask_server_uid:
            msg.kwargs['mask_client_uid'] = mask_server_uid
        else:
            print("WARNING: no mask has been built, scan will keep going...")
    return msg


def set_beamdump_suspender(xrun, suspend_thres=None, resume_thres=None,
                           wait_time=None, clear=True):
    """helper function to set suspender based on ring_current

    Parameters
    ----------
    xrun : instance of RunEngine
        the run engine instance suspender will be installed
    suspend_thres : float, optional
        suspend if ring current value falls below this threshold. ring
        current value is read out from ring current signal when
        set_beamdump_suspender function is executed. default is the
        larger value between 50 mA or 50% of ring current
    resume_thres : float, optional
        resume if ring current value falls below this threshold. ring
        current value is read out from ring current signal when
        set_beamdump_suspender function is executed. default is the
        larger value among 50 mA or 80% of current ring current
    wait_time : float, optional
        wait time in seconds after the resume condition is met. default
        is 1200s (20 mins)
    clear : bool, optional
        option on whether to clear all the existing suspender(s).
        default is True (only newly added suspender will be applied)
    """
    signal = xpd_configuration.get('ring_current', None)
    if signal is None:
        # edge case, attribute is accidentally removed
        raise RuntimeError("no ring current signal is found in "
                           "current configuration, please reach out to "
                           "local contact for more help.")
    signal_val = signal.get()
    default_suspend_thres = 50
    default_resume_thres = 50
    if suspend_thres is None:
        suspend_thres = max(default_suspend_thres, 0.5 * signal_val)
    if resume_thres is None:
        resume_thres = max(default_resume_thres, 0.8 * signal_val)
    if wait_time is None:
        wait_time = 1200
    if suspend_thres <= 50:
        warnings.warn("suspender set when beam current is low.\n"
                      "For the best operation, run:\n"
                      ">>> {}\n"
                      "when beam current is at its full value."
                      "To interrogate suspenders have"
                      " been installed, please run :\n"
                      ">>> {}\n"
                      .format("set_suspender(xrun)",
                              "xrun.suspenders"),
                      UserWarning)
    sus = SuspendFloor(signal, suspend_thres,
                       resume_thresh=resume_thres, sleep=wait_time)
    if clear:
        xrun.clear_suspenders()
    xrun.install_suspender(sus)
    print("INFO: suspender on signal {}, with suspend threshold {} and "
          "resume threshold={}, wait time ={}s has been installed.\n"
          .format(signal.name, suspend_thres, resume_thres, wait_time))


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
        if not glbl['is_simulation']:
            set_beamdump_suspender(self)

    def __call__(self, sample, plan, subs=None, *,
                 verify_write=False, dark_strategy=periodic_dark,
                 raise_if_interrupted=False, **metadata_kw):
        # The CustomizedRunEngine knows about a Beamtime object, and it
        # interprets integers for 'sample' as indexes into the Beamtime's
        # lists of Samples from all its Experiments.

        if isinstance(sample, int):
            try:
                sample = list(self.beamtime.samples.values())[sample]
            except IndexError:
                print("WARNING: hmm, there is no sample with index `{}`"
                      ", please do `bt.list()` to check if it exists yet"
                      .format(sample))
                return
        # If a plan is given as a string, look in up in the global registry.
        if isinstance(plan, int):
            try:
                plan = list(self.beamtime.scanplans.values())[plan]
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

        if glbl['shutter_control']:
            # Alter the plan to incorporate dark frames.
            # only works if user allows shutter control
            if glbl['auto_dark']:
                plan = dark_strategy(plan)
                plan = bp.msg_mutator(plan, _inject_qualified_dark_frame_uid)
            # force to close shutter after scan
            plan = bp.finalize_wrapper(plan,
                                       bp.abs_set(xpd_configuration['shutter'],
                                       XPD_SHUTTER_CONF['close'],
                                       wait=True)
                                       )

        # Load calibration file
        if glbl['auto_load_calib']:
            plan = bp.msg_mutator(plan, _inject_calibration_md)

        # Insert glbl mask
        #plan = bp.msg_mutator(plan, _inject_mask)
        plan = bp.msg_mutator(plan, _inject_mask_server_uid)

        # Insert xpdacq md version
        plan = bp.msg_mutator(plan, _inject_xpdacq_md_version)

        # Execute
        return super().__call__(plan, subs,
                                raise_if_interrupted=raise_if_interrupted,
                                **metadata_kw)
