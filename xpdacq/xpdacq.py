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
import typing
import uuid
import warnings
from collections import OrderedDict
from itertools import groupby
from pprint import pprint
from textwrap import indent
from typing import Generator

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import yaml
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks.broker import verify_files_saved
from bluesky.preprocessors import pchain
from bluesky.suspenders import SuspendFloor
from bluesky.utils import Msg, normalize_subs_input, single_gen
from ophyd import Device

from xpdacq.beamtime import (Beamtime, ScanPlan, close_shutter_stub,
                             open_shutter_stub)
from xpdacq.glbl import glbl
from xpdacq.preprocessors import (CalibPreprocessor, DarkPreprocessor,
                                  MaskPreprocessor, ShutterPreprocessor)
from xpdacq.tools import xpdAcqError, xpdAcqException
from xpdacq.xpdacq_conf import XPDACQ_MD_VERSION, xpd_configuration

Plan = typing.Generator[Msg, typing.Any, typing.Any]
MaskFiles = typing.List[typing.Tuple[Device, typing.List[str]]]
PoniFile = typing.List[typing.Tuple[Device, str]]
XPD_shutter = xpd_configuration.get("shutter")
PAUSE_MSG = """
Your RunEngine (xrun) is entering a paused state.
These are your options for changing the state of the RunEngine:

xrun.resume()    Resume the plan.
xrun.abort()     Perform cleanup, then kill plan. Mark exit_stats='aborted'.
xrun.stop()      Perform cleanup, then kill plan. Mark exit_status='success'.
xrun.halt()      Emergency Stop: Do not perform cleanup --- just stop.
"""


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
        if need_dark and (not qualified_dark_uid) and msg.command == "open_run" and (
            "dark_frame" not in msg.kwargs
        ):
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
        self.dark_preprocessors: typing.List[DarkPreprocessor] = []
        self.calib_preprocessors: typing.List[CalibPreprocessor] = []
        self.shutter_preprocessors: typing.List[ShutterPreprocessor] = []
        bec = BestEffortCallback()
        bec.noplot_streams.extend(["calib", "dark"])
        bec.disable_baseline()
        bec.disable_plots()
        bec.enable_heading()
        bec.enable_table()
        self.subscribe(bec)

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

    def _make_cpps(self, poni_file: PoniFile):
        cpps = []
        for det, poni in poni_file:
            cpp = CalibPreprocessor(det)
            cpp.load_calib_result({}, poni)
            cpps.append(cpp)
        return cpps

    def _make_mpps(self, mask_files: MaskFiles):
        mpps = []
        for det, masks in mask_files:
            mpp = MaskPreprocessor(det)
            mpp.load_masks(masks)
            mpps.append(mpp)
        return mpps

    def gen_plan(
        self,
        sample: typing.Union[int, str, dict, list, tuple],
        plan: typing.Union[int, str, typing.Generator, ScanPlan, list, tuple],
        robot: bool,
        poni_file: typing.Optional[PoniFile],
        mask_files: typing.Optional[MaskFiles]
    ) -> Plan:
        """_summary_

        Parameters
        ----------
        sample : typing.Union[int, str, dict, list, tuple]
            _description_
        plan : typing.Union[int, str, typing.Generator, ScanPlan, list, tuple]
            _description_
        robot : bool
            _description_

        Returns
        -------
        Plan
            _description_
        """
        # Translate the index of sample and plan to bluesky plan with metadata
        plan = xpdacq_composer(
            self.beamtime,
            sample,
            plan,
            robot=robot,
            shutter_control=None,
            dark_strategy=None,
            auto_load_calib=False
        )
        # create one time use cpp if poni_file is given
        cpps = self._make_cpps(poni_file) if poni_file is not None else self.calib_preprocessors
        # create one time use mask preprocessor if mask_files are given
        mpps = self._make_mpps(mask_files) if mask_files is not None else list()
        for cpp in cpps:
            plan = cpp(plan)
        for dpp in self.dark_preprocessors:
            plan = dpp(plan)
        for spp in self.shutter_preprocessors:
            plan = spp(plan)
        for mpp in mpps:
            plan = mpp(plan)
        return plan

    def __call__(
        self,
        sample: typing.Union[int, str, dict, list, tuple],
        plan: typing.Union[int, str, typing.Generator, ScanPlan, list, tuple],
        subs: typing.Union[typing.Callable, dict, list] = None,
        *,
        poni_file: PoniFile = None,
        mask_files: MaskFiles = None,
        verify_write: bool = False,
        dark_strategy: typing.Callable = None,
        robot: bool = False,
        ask_before_run: bool = False,
        **metadata_kw
    ):
        """
        Execute a plan.

        The call is basically the same as the RE. The only difference is that the plan will be mutated and
        preprocessed to incorpate sample meta-data, dark fram stragy and so on. Any keyword arguments other than
        those listed below will be interpreted as metadata and recorded with the run.

        Parameters
        ----------
        sample : int or dict-like or list of int or dict-like Sample metadata

            If a beamtime object is linked, an integer will be interpreted as the index appears
            in the ``bt.list()`` method, corresponding metadata will be
            passed. A customized dict can also be passed as the sample metadata.

        plan : int or generator or list of int or generator

            Scan plan. If a beamtime object is linked, an integer will be interpreted as the index appears in
            the ``bt.list()`` method, corresponding scan plan will be A generator or that yields ``Msg`` objects
            (or an iterable that returns such a generator) can also be passed.

        subs: callable, list, or dict, optional

            Temporary subscriptions (a.k.a. callbacks) to be used on this run. Default to None. For convenience,
            any of the following are accepted:

            * a callable, which will be subscribed to 'all'
            * a list of callables, which again will be subscribed to 'all'
            * a dictionary, mapping specific subscriptions to callables or
              lists of callables; valid keys are {'all', 'start', 'stop',
              'event', 'descriptor'}

        poni_file: str

            The path to a poni file. This poni file will be read and the data in it will be in the `calib`
            stream instead of the data in the registered CalibPreprocessors. This is only for one time use.

        mask_files: List[str]

            A list of the paths to mask files. The mask convention is 0 good other bad. The masks will be
            overlay (sum up) to create a sinlge mask and this mask will be in the `mask` event stream.

        verify_write: bool, optional

            Double check if the data have been written into database. In general data is written in a lossless
            fashion at the NSLS-II. Therefore, False by default.

        dark_strategy: callable, optional. (deprecated)

            Protocol of taking dark frame during experiment. Default to the logic of matching dark frame and
            light frame with the sample exposure time and frame rate. Details can be found at
            ``http://xpdacq.github.io/xpdAcq/usb_Running.html#automated-dark-collection``

        robot: bool, optional

            If true run the scan as a robot scan, defaults to False

        metadata_kw:

            Extra keyword arguments for specifying metadata in the run time. If the extra metdata has the same
            key as the ``sample``, ``ValueError`` will be raised.

        Returns
        -------
        uids : list

            list of uids (i.e. RunStart Document uids) of run(s)
        """
        if dark_strategy is not None:
            raise Warning("dark_strategy is deprecated.")
        if self.md.get("robot", None) is not None:
            raise RuntimeError(
                "Robot must be specified at call time, not in"
                "global metadata"
            )
        # compose the plan
        final_plan = self.gen_plan(sample, plan, robot, poni_file, mask_files)
        # normalize the subs
        _subs = normalize_subs_input(subs) if subs else {}
        # verify writing files
        if verify_write:
            _subs.update({"stop": verify_files_saved})
        if robot:
            metadata_kw.update({'robot': True})
        if ask_before_run:
            ip = input("Is this ok? [y]/n")
            if ip.lower() == "n":
                return
        return super(CustomizedRunEngine, self).__call__(final_plan, _subs, **metadata_kw)


def xpdacq_composer(
    beamtime: Beamtime,
    sample: typing.Union[int, dict, typing.List[int]],
    plan: typing.Union[int, Generator, typing.List[int], typing.Generator],
    *,
    robot: bool = False,
    shutter_control: typing.Tuple[Device, typing.Any] = None,
    dark_strategy: typing.Callable = None,
    auto_load_calib: bool = False
) -> typing.Generator:
    """Create a list of plans for an xpd experiment. Used in `~xpdacq.xpdacq.CumstomeizedRunEngine.__call__`.

    Parameters
    ----------
    beamtime :
        The beamtime object.

    sample :
        If a beamtime object is linked, an integer will be interpreted as the index appears in the ``bt.list()``
        method, corresponding metadata will be passed. A customized dict can also be passed as the sample
        metadata.

    plan :
        Scan plan. If a beamtime object is linked, an integer will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding scan plan will be A generator or that yields ``Msg`` objects (or an
        iterable that returns such a generator) can also be passed.

    robot :
        If True, the plan is meant to be using robot.

    shutter_control :
        A tuple of the shutter device and its close state. The shutter will be closed after the whole scan.
        If None, shutter won't be controlled and no dark will be taken.

    dark_strategy :
        The strategy how to take the dark frame.

    auto_load_calib :
        If True, the calibration meta-data will be injected into the run. Else, do nothing.

    Returns
    -------
    grand_plan :
        The grand plan to be run by the RunEngine.
    """
    # check wavelength
    warn_wavelength(beamtime)
    # noramlize the sample and plan to two lists with the same length
    lst_sample, lst_plan = _normalize_sample_plan(sample, plan)
    # Turn ints into actual sample dictionary
    lst_metadata = [translate_to_sample(beamtime, s) for s in lst_sample]
    # Turn ints into bluesky generators
    lst_bp_plan = [translate_to_plan(beamtime, p) for p in lst_plan]
    # Make the complete plan by chaining the chained plans
    if robot:
        lst_bp_plan = gen_robot_plans(beamtime, lst_metadata, lst_bp_plan)
    # Inject the sample metadata
    lst_bp_plan = [inject_metadata(p, s) for p, s in zip(lst_bp_plan, lst_metadata)]
    # chain the plans
    grand_plan = pchain(*lst_bp_plan)
    # shutter control and dark
    if shutter_control and dark_strategy:
        grand_plan = dark_strategy(grand_plan)
        grand_plan = bpp.msg_mutator(grand_plan, _inject_qualified_dark_frame_uid)
    # Load calibration file
    if auto_load_calib:
        grand_plan = bpp.msg_mutator(grand_plan, _inject_calibration_md)
    # Insert xpdacq md version
    grand_plan = bpp.msg_mutator(grand_plan, _inject_xpdacq_md_version)
    # Insert analysis stage tag
    grand_plan = bpp.msg_mutator(grand_plan, _inject_analysis_stage)
    # Insert filter metadata
    grand_plan = bpp.plan_mutator(grand_plan, _inject_filter_positions)
    # close shutter
    if shutter_control:
        shutter, close_state = shutter_control
        grand_plan = bpp.finalize_wrapper(grand_plan, close_shutter_at_last(shutter, close_state))
    return grand_plan


def close_shutter_at_last(plan: typing.Generator, shutter: Device, close_state: typing.Any) -> typing.Generator:
    """Close the shutter at the end of the plan."""
    return bpp.finalize_wrapper(plan, bps.mv(shutter, close_state))


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
    print("opening shutter...")


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
                "recorded in {}".format(calib_yaml_name)
            )
        return calib_dict


def inject_metadata(plan: typing.Generator, metadata: dict) -> typing.Generator:
    """Inject the metadata into a plan."""

    def _inject_metadata(msg: Msg):
        """Inject metadata in the start of the run."""
        if msg.command == "open_run":
            msg.kwargs.update(**metadata)
        return msg

    plan1 = bpp.msg_mutator(plan, _inject_metadata)
    return plan1


def __inject_filter_positions(msg):
    filter_bank = xpd_configuration["filter_bank"]
    filter_status = dict()
    for name in filter_bank.read_attrs:
        flt = getattr(filter_bank, name)
        sts = (yield from bps.rd(flt))
        filter_status[name] = sts
    print("INFO: Current filter status")
    for name, status in filter_status.items():
        print("INFO: {} : {}".format(name, status))
    msg.kwargs["filter_positions"] = filter_status
    return (yield msg)


def _inject_filter_positions(msg):
    """Inject the filter position in start."""
    if msg.command == "open_run":
        return __inject_filter_positions(msg), None
    return None, None


def _inject_qualified_dark_frame_uid(msg):
    """Inject the dark frame uid in start."""
    if msg.command == "open_run" and msg.kwargs.get("dark_frame") is not True:
        dark_uid = _validate_dark(glbl["dk_window"])
        msg.kwargs["sc_dk_field_uid"] = dark_uid
    return msg


def _inject_calibration_md(msg):
    """Inject the calibration data in start."""
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


# For convenience, define short plans the use these custom commands.

def load_sample(position, geometry=None):
    """For robot."""
    return (
        yield from single_gen(
            Msg("load_sample", xpd_configuration["robot"], position, geometry)
        )
    )


def unload_sample():
    """For robot."""
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


def translate_to_sample(
    beamtime: Beamtime,
    sample: typing.Union[int, str, dict]
) -> typing.Union[dict, typing.List[dict]]:
    """Translate a sample into a dictionary.

    Parameters
    ----------
    beamtime :
        The BeamTime instance.

    sample :
        Sample metadata. If a beamtime object is linked,
        an integer will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding metadata will be passed.
        A customized dict can also be passed as the sample
        metadata.

    Returns
    -------
    sample_md :
        The sample info loaded
    """
    if isinstance(sample, int):
        try:
            return dict(beamtime.samples.sel(sample))
        except IndexError:
            raise xpdAcqError(
                "ERROR: hmm, there is no sample with index `{}`"
                ", please do `bt.list()` to check if it exists yet".format(
                    sample
                )
            )
    elif isinstance(sample, str):
        try:
            return dict(beamtime.samples[sample])
        except KeyError:
            raise xpdAcqError(
                "ERROR: hmm, there is no sample with key `{}`"
                ", please do `bt.list()` to check if it exists yet".format(
                    sample
                )
            )
    elif isinstance(sample, OrderedDict):
        return dict(sample)
    elif isinstance(sample, dict):
        return sample
    else:
        raise TypeError(f"The type of sample is {type(sample)}. Expect int, str, dict.")


def translate_to_plan(beamtime: Beamtime, plan: typing.Union[int, str, ScanPlan]) -> typing.Generator:
    """Translate a plan input into a generator.

    Parameters
    ----------
    beamtime : Beamtime
        The BeamTime instance.

    plan : int, str, or dict-like
        Scan plan. If a beamtime object is linked, an integer
        will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding scan plan will be
        A generator or that yields ``Msg`` objects (or an iterable
        that returns such a generator) can also be passed.

    Returns
    -------
    plan : generator
        The generator of messages for the plan。
    """
    # If a plan is given as a int, look in up in the global registry.
    if isinstance(plan, int):
        try:
            scanplan = beamtime.scanplans.sel(plan)
            return scanplan.factory()
        except IndexError:
            raise xpdAcqError(
                "ERROR: hmm, there is no scanplan with index `{}`"
                ", please do `bt.list()` to check if it exists yet".format(
                    plan
                )
            )
    # If the plan is an xpdAcq 'ScanPlan', make the actual plan.
    elif isinstance(plan, str):
        try:
            scanplan = beamtime.scanplans[plan]
            return scanplan.factory()
        except KeyError:
            raise xpdAcqError(
                "ERROR: hmm, there is no scanplan with key `{}`"
                ", please do `bt.list()` to check if it exists yet".format(
                    plan
                )
            )
    elif isinstance(plan, ScanPlan):
        return plan.factory()
    elif isinstance(plan, Generator):
        return plan
    else:
        raise TypeError(f"The type of plan is {type(plan)}. Expect int, str, ScanPlan or generator.")


def _normalize_sample_plan(sample, plan) -> typing.Tuple[list, list]:
    """Normalize samples and plans to list of samples and plans

    Parameters
    ----------
    sample :

        Sample metadata. If a beamtime object is linked, an integer will be interpreted as the index appears in
        the ``bt.list()`` method, corresponding metadata will be passed. A customized dict can also be passed as
        the sample metadata.

    plan :

        Scan plan. If a beamtime object is linked, an integer will be interpreted as the index appears in the
        ``bt.list()`` method, corresponding scan plan will be A generator or that yields ``Msg`` objects (or an
        iterable that returns such a generator) can also be passed.

    Returns
    -------
    sample :

        The list of samples

    plan :

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


def print_plans(
    beamtime: Beamtime,
    sample: typing.List[dict],
    plan: typing.List[typing.Generator],
    robot: bool = False
) -> None:
    """Print the plan for each sample."""
    print("This is the current experimental plan:")
    print("Sample Name: Sample Position")
    for s, p in group_by_sample(sample, plan):
        if s:
            pos = beamtime.robot_info[s["sa_uid"]] if robot else ""
            print(s["sample_name"], ":", pos)
        for pp in p:
            # Check if this is a registered scanplan
            if isinstance(pp, int):
                print(
                    indent("{}".format(list(beamtime.scanplans.values())[pp]), "\t")
                )
            else:
                print(
                    "This scan is not a registered scanplan so no summary."
                )
    return


def gen_robot_plans(beamtime: Beamtime, sample: list, plan: list) -> typing.List[Generator]:
    """Create plan for robot."""
    total_plan = []
    for s, p in zip(sample, plan):
        # If robot scan inject the needed md into the sample
        s.update(beamtime.robot_info[s["sa_uid"]])
        total_plan.append(robot_wrapper(p, s))
    return total_plan


def group_by_sample(sample: list, plan: list) -> typing.Generator:
    """Group the sample and plan by sample. Return sample, a list of plans."""
    for k, v in groupby(zip(sample, plan), key=lambda x: x[0]):
        yield k, [o[1] for o in v]


def warn_wavelength(beamtime: Beamtime, key: str = "bt_wavelength") -> None:
    """Warning if no wavelength in beamtime."""
    if beamtime and beamtime.get(key) is None:
        print(
            "WARNING: there is no wavelength information in current"
            "beamtime object, scan will keep going...."
        )
