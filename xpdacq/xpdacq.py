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
import time
import uuid
import warnings
from itertools import groupby
from pprint import pprint
from textwrap import indent

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import yaml
from bluesky import RunEngine
from bluesky.callbacks.broker import verify_files_saved
from bluesky.preprocessors import pchain
from bluesky.suspenders import SuspendFloor
from bluesky.utils import normalize_subs_input, single_gen, Msg
from xpdconf.conf import XPD_SHUTTER_CONF

from xpdacq.beamtime import ScanPlan, close_shutter_stub, open_shutter_stub
from xpdacq.glbl import glbl
from xpdacq.tools import xpdAcqException
from xpdacq.xpdacq_conf import xpd_configuration, XPDACQ_MD_VERSION

XPD_shutter = xpd_configuration.get("shutter")


def _update_dark_dict_list(name, doc):
    """ generate dark frame reference

    This function should be subscribed to 'stop' documents from dark
    frame runs.
    """
    # always grab from glbl state
    dark_dict_list = list(glbl["_dark_dict_list"])
    # obtain light count time that is already set to area_det
    area_det = xpd_configuration["area_det"]
    acq_time = area_det.cam.acquire_time.get()
    if hasattr(area_det, 'images_per_set'):
        num_frame = area_det.images_per_set.get()
    else:
        num_frame = 1
    light_cnt_time = acq_time * num_frame

    dark_dict = {}
    dark_dict["acq_time"] = acq_time
    dark_dict["exposure"] = light_cnt_time
    dark_dict["timestamp"] = doc["time"]
    dark_dict["uid"] = doc["run_start"]
    if doc["exit_status"] == "success":
        print("dark frame complete, update dark dict")
        dark_dict_list.append(dark_dict)
        glbl["_dark_dict_list"] = dark_dict_list  # update glbl._dark_dict_list
    else:
        # FIXME: replace with logging and detailed warning next PR
        print(
            "INFO: dark scan was not successfully executed.\n"
            "gobal dark frame information will not be updated!"
        )


def take_dark():
    """a plan for taking a single dark frame"""
    print("INFO: closing shutter...")
    yield from close_shutter_stub()
    print("INFO: taking dark frame....")
    # upto this stage, area_det has been configured to so exposure time is
    # correct
    area_det = xpd_configuration["area_det"]
    acq_time = area_det.cam.acquire_time.get()
    if hasattr(area_det, 'images_per_set'):
        num_frame = area_det.images_per_set.get()
    else:
        num_frame = 1
    computed_exposure = acq_time * num_frame
    # update md
    _md = {
        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_computed_exposure": computed_exposure,
        "sp_type": "ct",
        "sp_plan_name": "dark_{}".format(computed_exposure),
        "dark_frame": True,
    }
    c = bp.count([area_det], md=_md)
    yield from bpp.subs_wrapper(c, {"stop": [_update_dark_dict_list]})
    # TODO: remove this, since it kinda depends on what happens next?
    print("opening shutter...")


def periodic_dark(plan):
    """
    a plan wrapper that takes a plan and inserts `take_dark`

    The `take_dark` plan is inserted on the fly before the beginning of
    any new run after a period of time defined by glbl['dk_window'] has passed.
    """
    need_dark = True

    def insert_take_dark(msg):
        nonlocal need_dark
        qualified_dark_uid = _validate_dark(expire_time=glbl["dk_window"])
        area_det = xpd_configuration["area_det"]

        if (not need_dark) and (not qualified_dark_uid):
            need_dark = True
        if need_dark and (not qualified_dark_uid) and msg.command == "open_run" and \
                ("dark_frame" not in msg.kwargs):
            # We are about to start a new 'run' (e.g., a count or a scan).
            # Insert a dark frame run first.
            need_dark = False
            # Annoying detail: the detector was probably already staged.
            # Unstage it (if it wasn't staged, nothing will happen) and
            # then take_dark() and then re-stage it.
            return (
                bpp.pchain(
                    bps.unstage(area_det),
                    take_dark(),
                    bps.stage(area_det),
                    bpp.single_gen(msg),
                    open_shutter_stub(),
                ),
                None,
            )
        elif msg.command == "open_run" and "dark_frame" not in msg.kwargs:
            return (
                bpp.pchain(
                    bpp.single_gen(msg),
                    open_shutter_stub()
                ),
                None,
            )
        else:
            # do nothing if (not need_dark)
            return None, None

    return (yield from bpp.plan_mutator(plan, insert_take_dark))


def _validate_dark(expire_time=None):
    """find appropriate dark frame uid stored in dark_dict_list

    element in dark_scan_dict is expected to be a dict with following
    keys: 'exposure', 'uid' and 'timestamp'
    """
    if expire_time is None:
        expire_time = glbl["dk_window"]
    dark_dict_list = glbl["_dark_dict_list"]
    # if glbl.dark_dict_list = None, do a dark anyway
    if not dark_dict_list:
        return None
    # obtain light count time that is already set to pe1c
    area_det = xpd_configuration["area_det"]
    acq_time = area_det.cam.acquire_time.get()
    if hasattr(area_det, 'images_per_set'):
        num_frame = area_det.images_per_set.get()
    else:
        num_frame = 1
    light_cnt_time = acq_time * num_frame
    # find fresh and qualified dark
    now = time.time()
    qualified_dark_list = []
    for el in dark_dict_list:
        expo_diff = abs(el["exposure"] - light_cnt_time)
        time_diff = abs(el["timestamp"] - now)
        if (expo_diff < acq_time) and (time_diff < expire_time * 60) and (el["acq_time"] == acq_time):
            qualified_dark_list.append((el.get("uid"), expo_diff, time_diff))
    if qualified_dark_list:
        # sort wrt expo_diff and time_diff for best candidate
        # best_dark = sorted(qualified_dark_list,
        #                   key=lambda x: x[1] and x[2])[0]
        best_dark = sorted(qualified_dark_list, key=lambda x: x[2])[0]
        best_dark_uid = best_dark[0]
        return best_dark_uid
    else:
        return None


def show_calib():
    """helper function to print currnt calibration params

    Returns
    -------
    None
    """
    calib_md = _auto_load_calibration_file(in_scan=False)
    if calib_md:
        pprint(calib_md)
    else:
        print("INFO: no calibration has been perfomed yet")


def _auto_load_calibration_file(in_scan=True):
    """function to load the most recent calibration file in config_base

    Returns
    -------
    calib_dict : dict
    dictionary contains calibration parameters computed by pyFAI
    and file name of the most recent calibration. If no calibration
    file exits in xpdUser/config_base, returns None.
    """

    config_dir = glbl["config_base"]
    if not os.path.isdir(config_dir):
        raise xpdAcqException(
            "WARNING: Required directory {} doesn't"
            " exist, did you accidentally delete it?".format(config_dir)
        )
    calib_yaml_name = os.path.join(config_dir, glbl["calib_config_name"])
    # no calib, skip
    if not os.path.isfile(calib_yaml_name):
        if in_scan:
            print(
                "INFO: No calibration file found in config_base.\n"
                "Scan will still keep going on...."
            )
        return
    else:
        with open(calib_yaml_name) as f:
            calib_dict = yaml.unsafe_load(f)
        if in_scan:
            print(
                "INFO: This scan will append calibration parameters "
                "recorded in {}".format(calib_dict["poni_file_name"])
            )
        return calib_dict


def _inject_filter_positions(msg):
    if msg.command == "open_run":
        filter_bank = xpd_configuration["filter_bank"]
        filters = filter_bank.read_attrs
        print("INFO: Current filter status")
        for el in filters:
            print("INFO: {} : {}".format(el, getattr(filter_bank, el).value))
        msg.kwargs["filter_positions"] = {
            fltr: getattr(filter_bank, fltr).value for fltr in filters
        }
    return msg


def _inject_qualified_dark_frame_uid(msg):
    if msg.command == "open_run" and msg.kwargs.get("dark_frame") is not True:
        dark_uid = _validate_dark(glbl["dk_window"])
        msg.kwargs["sc_dk_field_uid"] = dark_uid
    return msg


def _inject_calibration_md(msg):
    if msg.command == "open_run":
        exp_hash_uid = glbl.get("exp_hash_uid")
        # inject client uid to all runs
        msg.kwargs.update({"detector_calibration_client_uid": exp_hash_uid})
        if "is_calibration" in msg.kwargs:
            # inject server uid if it's calibration run
            msg.kwargs.update(
                {"detector_calibration_server_uid": exp_hash_uid}
            )
        else:
            # load calibration param if exists
            calibration_md = _auto_load_calibration_file()
            if calibration_md:
                injected_calib_dict = dict(calibration_md)
                # inject calibration md
                msg.kwargs["calibration_md"] = injected_calib_dict
    return msg


def _inject_xpdacq_md_version(msg):
    """simply insert xpdAcq md version"""
    if msg.command == "open_run":
        msg.kwargs["xpdacq_md_version"] = XPDACQ_MD_VERSION
    return msg


def _inject_analysis_stage(msg):
    """specify at which stage the documents is processed"""
    if msg.command == "open_run":
        msg.kwargs["analysis_stage"] = "raw"
    return msg


def _sample_injector_factory(sample):
    """Factory for message mutators which inject the sample metadata

    Parameters
    ----------
    sample : dict
        The sample metadata

    Returns
    -------
    _inject_sample_md : func
        The message mutator

    """

    def _inject_sample_md(msg):
        if msg.command == "open_run":
            # No keys in metadata_kw are allows to collide with sample keys.
            if set(sample) & set(msg.kwargs):
                raise ValueError(
                    "These keys in metadata_kw are illegal "
                    "because they are always in sample: "
                    "{}".format(set(sample) & set(msg.kwargs))
                )

            msg.kwargs.update(sample)
        return msg

    return _inject_sample_md


def update_experiment_hash_uid():
    """helper function to assign new uid to glbl state"""
    new_uid = str(uuid.uuid4())
    glbl["exp_hash_uid"] = new_uid
    print("INFO: experiment hash uid as been updated to " "{}".format(new_uid))

    return new_uid


def set_beamdump_suspender(
    xrun, suspend_thres=None, resume_thres=None, wait_time=None, clear=True
):
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
    signal = xpd_configuration.get("ring_current", None)
    if signal is None:
        # edge case, attribute is accidentally removed
        raise RuntimeError(
            "no ring current signal is found in "
            "current configuration, please reach out to "
            "local contact for more help."
        )
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
        warnings.warn(
            "suspender set when beam current is low.\n"
            "For the best operation, run:\n"
            ">>> {}\n"
            "when beam current is at its full value."
            "To interrogate suspenders have"
            " been installed, please run :\n"
            ">>> {}\n".format("set_suspender(xrun)", "xrun.suspenders"),
            UserWarning,
        )
    sus = SuspendFloor(
        signal, suspend_thres, resume_thresh=resume_thres, sleep=wait_time
    )
    if clear:
        xrun.clear_suspenders()
    xrun.install_suspender(sus)
    print(
        "INFO: suspender on signal {}, with suspend threshold {} and "
        "resume threshold={}, wait time ={}s has been installed.\n".format(
            signal.name, suspend_thres, resume_thres, wait_time
        )
    )


PAUSE_MSG = """
Your RunEngine (xrun) is entering a paused state.
These are your options for changing the state of the RunEngine:

xrun.resume()    Resume the plan.
xrun.abort()     Perform cleanup, then kill plan. Mark exit_stats='aborted'.
xrun.stop()      Perform cleanup, then kill plan. Mark exit_status='success'.
xrun.halt()      Emergency Stop: Do not perform cleanup --- just stop.
"""


class CustomizedRunEngine(RunEngine):
    """A RunEngine customized for XPD workflows.

    Parameters
    ----------
    beamtime : xpdacq.beamtime.Beamtime or None
        beamtime object that will be linked to. This beamtime object
        provide reference of sample and scanplan indicies. If no
        beamtime object is linked, index-based syntax will not be allowed.

    Attributes
    ----------
    beamtime
        beamtime object currently associated with this RunEngine instance.

    Examples
    --------
    Basic usage: run samples and plans by number

    >>> xrun(0, 0)

    Advanced usage: use custom plan which is compatible with bluesky

    >>> xrun(3, custom_plan)  # sample 3, an arbitrary bluesky plan

    Or custom sample info. sample just has to be dict-like
    and contain the required keys.

    >>> xrun(custom_sample_dict, custom_plan)

    Or use completely custom dark frame logic

    >>> xrun(3, custom_plan, dark_strategy=some_custom_func)
    """

    def __init__(self, beamtime, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._beamtime = beamtime
        self.pause_msg = PAUSE_MSG

    @property
    def beamtime(self):
        if self._beamtime is None:
            raise RuntimeError(
                "Your beamtime environment is not properly "
                "setup. Please do\n"
                ">>> xrun.beamtime = bt\n"
                "then retry"
            )
        return self._beamtime

    @beamtime.setter
    def beamtime(self, bt_obj):
        self._beamtime = bt_obj
        self.md.update(bt_obj.md)
        print("INFO: beamtime object has been linked\n")
        if not glbl["is_simulation"]:
            set_beamdump_suspender(self)
        # assign hash of experiment condition
        exp_hash_uid = str(uuid.uuid4())
        glbl["exp_hash_uid"] = exp_hash_uid

    def translate_to_sample(self, sample):
        """Translate a sample into a list of dict

        Parameters
        ----------
        sample : list of int or dict-like
            Sample metadata. If a beamtime object is linked,
            an integer will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding metadata will be passed.
            A customized dict can also be passed as the sample
            metadata.

        Returns
        -------
        sample : list of dict
            The sample info loaded
        """
        if isinstance(sample, list):
            sample = [self.translate_to_sample(s) for s in sample]
        if isinstance(sample, int):
            try:
                sample = list(self.beamtime.samples.values())[sample]
            except IndexError:
                print(
                    "WARNING: hmm, there is no sample with index `{}`"
                    ", please do `bt.list()` to check if it exists yet".format(
                        sample
                    )
                )
                return
        return sample

    def translate_to_plan(self, plan, sample):
        """Translate a plan input into a generator

        Parameters
        ----------
        sample : list of int or dict-like
            Sample metadata. If a beamtime object is linked,
            an integer will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding metadata will be passed.
            A customized dict can also be passed as the sample
            metadata.
        plan : list of int or generator
            Scan plan. If a beamtime object is linked, an integer
            will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding scan plan will be
            A generator or that yields ``Msg`` objects (or an iterable
            that returns such a generator) can also be passed.

        Returns
        -------
        plan : generator
            The generator of messages for the plan

        """
        if isinstance(plan, list):
            plan = [self.translate_to_plan(p, s) for p, s in zip(plan, sample)]
        # If a plan is given as a int, look in up in the global registry.
        else:
            if isinstance(plan, int):
                try:
                    plan = list(self.beamtime.scanplans.values())[plan]
                except IndexError:
                    print(
                        "WARNING: hmm, there is no scanplan with index `{}`"
                        ", please do `bt.list()` to check if it exists yet".format(
                            plan
                        )
                    )
                    return
            # If the plan is an xpdAcq 'ScanPlan', make the actual plan.
            if isinstance(plan, ScanPlan):
                plan = plan.factory()
            mm = _sample_injector_factory(sample)
            plan = bpp.msg_mutator(plan, mm)
        return plan

    def _normalize_sample_plan(self, sample, plan):
        """Normalize samples and plans to list of samples and plans

        Parameters
        ----------
        sample : int or dict-like or list of int or dict-like
            Sample metadata. If a beamtime object is linked,
            an integer will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding metadata will be passed.
            A customized dict can also be passed as the sample
            metadata.
        plan : int or generator or list of int or generator
            Scan plan. If a beamtime object is linked, an integer
            will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding scan plan will be
            A generator or that yields ``Msg`` objects (or an iterable
            that returns such a generator) can also be passed.

        Returns
        -------
        sample : list of samples
            The list of samples
        plan : list of plans
            The list of plans

        """
        if isinstance(sample, list) and not isinstance(plan, list):
            plan = [plan] * len(sample)
        elif not isinstance(sample, list) and isinstance(plan, list):
            sample = [sample] * len(plan)
        elif not isinstance(sample, list) and not isinstance(plan, list):
            plan = [plan]
            sample = [sample]
        if len(sample) != len(plan):
            raise RuntimeError("Samples and Plans must be the same length")
        return sample, plan

    def __call__(
        self, sample, plan, subs=None, *, verify_write=False, dark_strategy=periodic_dark, robot=False,
        **metadata_kw
    ):
        """
        Execute a plan

        Any keyword arguments other than those listed below will
        be interpreted as metadata and recorded with the run.

        Parameters
        ----------
        sample : int or dict-like or list of int or dict-like
            Sample metadata. If a beamtime object is linked,
            an integer will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding metadata will be passed.
            A customized dict can also be passed as the sample
            metadata.
        plan : int or generator or list of int or generator
            Scan plan. If a beamtime object is linked, an integer
            will be interpreted as the index appears in the
            ``bt.list()`` method, corresponding scan plan will be
            A generator or that yields ``Msg`` objects (or an iterable
            that returns such a generator) can also be passed.
        subs: callable, list, or dict, optional
            Temporary subscriptions (a.k.a. callbacks) to be used on
            this run. Default to None. For convenience, any of the
            following are accepted:

            * a callable, which will be subscribed to 'all'
            * a list of callables, which again will be subscribed to 'all'
            * a dictionary, mapping specific subscriptions to callables or
              lists of callables; valid keys are {'all', 'start', 'stop',
              'event', 'descriptor'}

        verify_write: bool, optional
            Double check if the data have been written into database.
            In general data is written in a lossless fashion at the
            NSLS-II. Therefore, False by default.
        dark_strategy: callable, optional.
            Protocol of taking dark frame during experiment. Default
            to the logic of matching dark frame and light frame with
            the sample exposure time and frame rate. Details can be
            found at ``http://xpdacq.github.io/xpdAcq/usb_Running.html#automated-dark-collection``
        robot: bool, optional
            If true run the scan as a robot scan, defaults to False
        metadata_kw:
            Extra keyword arguments for specifying metadata in the
            run time. If the extra metdata has the same key as the
            ``sample``, ``ValueError`` will be raised.

        Returns
        -------
        uids : list
            list of uids (i.e. RunStart Document uids) of run(s)
        """
        if self.md.get("robot", None) is not None:
            raise RuntimeError(
                "Robot must be specified at call time, not in"
                "global metadata"
            )
        if robot:
            metadata_kw.update(robot=True)
        # The CustomizedRunEngine knows about a Beamtime object, and it
        # interprets integers for 'sample' as indexes into the Beamtime's
        # lists of Samples from all its Experiments.

        # Turn everything into lists
        sample, plan = self._normalize_sample_plan(sample, plan)
        # Turn ints into actual samples
        sample = self.translate_to_sample(sample)
        if robot:
            print("This is the current experimental plan:")
            print("Sample Name: Sample Position")
            for s, p in [
                (k, [o[1] for o in v])
                for k, v in groupby(zip(sample, plan), key=lambda x: x[0])
            ]:
                print(
                    s["sample_name"],
                    ":",
                    self._beamtime.robot_info[s["sa_uid"]],
                )
                for pp in p:
                    # Check if this is a registered scanplan
                    if isinstance(pp, int):
                        print(
                            indent(
                                "{}".format(
                                    list(self.beamtime.scanplans.values())[pp]
                                ),
                                "\t",
                            )
                        )
                    else:
                        print(
                            "This scan is not a registered scanplan so no "
                            "summary"
                        )
            ip = input("Is this ok? [y]/n")
            if ip.lower() == "n":
                return
        # Turn ints into generators
        plan = self.translate_to_plan(plan, sample)

        # Collect the plans by contiguous samples and chain them
        sample, plan = zip(
            *[
                (k, pchain(*[o[1] for o in v]))
                for k, v in groupby(zip(sample, plan), key=lambda x: x[0])
            ]
        )

        # Make the complete plan by chaining the chained plans
        total_plan = []
        for s, p in zip(sample, plan):
            if robot:
                # If robot scan inject the needed md into the sample
                s.update(self._beamtime.robot_info[s["sa_uid"]])
                total_plan.append(robot_wrapper(p, s))
            else:
                total_plan.append(p)
        plan = pchain(*total_plan)

        _subs = normalize_subs_input(subs)
        if verify_write:
            _subs.update({"stop": verify_files_saved})

        if self._beamtime and self._beamtime.get("bt_wavelength") is None:
            print(
                "WARNING: there is no wavelength information in current"
                "beamtime object, scan will keep going...."
            )

        if glbl["shutter_control"]:
            # Alter the plan to incorporate dark frames.
            # only works if user allows shutter control
            if glbl["auto_dark"]:
                plan = dark_strategy(plan)
                plan = bpp.msg_mutator(plan, _inject_qualified_dark_frame_uid)
            # force to close shutter after scan
            plan = bpp.finalize_wrapper(
                plan,
                bps.abs_set(
                    xpd_configuration["shutter"],
                    XPD_SHUTTER_CONF["close"],
                    wait=True,
                ),
            )

        # Load calibration file
        if glbl["auto_load_calib"]:
            plan = bpp.msg_mutator(plan, _inject_calibration_md)
        # Insert xpdacq md version
        plan = bpp.msg_mutator(plan, _inject_xpdacq_md_version)
        # Insert analysis stage tag
        plan = bpp.msg_mutator(plan, _inject_analysis_stage)
        # Insert filter metadata
        plan = bpp.msg_mutator(plan, _inject_filter_positions)

        # Execute
        return super().__call__(plan, subs, **metadata_kw)


# For convenience, define short plans the use these custom commands.


def load_sample(position, geometry=None):
    # TODO: I think this can be simpler.
    return (
        yield from single_gen(
            Msg("load_sample", xpd_configuration["robot"], position, geometry)
        )
    )


def unload_sample():
    # TODO: I think this can be simpler.
    return (
        yield from single_gen(Msg("unload_sample", xpd_configuration["robot"]))
    )


# These are usable bluesky plans.


def robot_wrapper(plan, sample):
    """Wrap a plan in load/unload messages.
    Parameters
    ----------
    plan : a bluesky plan
    sample : dict
        must contain 'position'; optionally also 'geometry'
    Example
    -------
    >>> plan = count([pe1c])
    >>> new_plan = robot_wrapper(plan, {'position': 1})
    """
    yield from bps.checkpoint()
    yield from load_sample(sample['robot_identifier'],
                           sample.get('robot_geometry', None))
    yield from bps.checkpoint()
    yield from plan
    yield from bps.checkpoint()
    yield from unload_sample()
    yield from bps.checkpoint()
