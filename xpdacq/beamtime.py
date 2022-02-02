#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Dan Allan
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import inspect
import os
import typing
import uuid
from abc import ABC
from collections import ChainMap, OrderedDict

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import numpy as np
import pyFAI
import yaml
from bluesky.callbacks import LiveTable
from xpdconf.conf import XPD_SHUTTER_CONF

from .glbl import glbl
from .tools import regularize_dict_key
from .validated_dict import ValidatedDictLike
from .xpdacq_conf import xpd_configuration
from .yamldict import YamlDict, YamlChainMap

# This is used to map plan names (strings in the YAML file) to actual
# plan functions in Python.
_PLAN_REGISTRY = {}


class PlanError(Exception):
    pass


def register_plan(plan_name, plan_func, overwrite=False):
    """
    Map between a plan_name (string) and a plan_func (generator function).
    """
    if plan_name in _PLAN_REGISTRY and not overwrite:
        raise KeyError(
            "A plan is already registered by this name. Use "
            "overwrite=True to overwrite it."
        )
    _PLAN_REGISTRY[plan_name] = plan_func


def unregister_plan(plan_name):
    del _PLAN_REGISTRY[plan_name]


def _summarize(plan):
    """based on bluesky.utils.print_summary"""
    output = []
    read_cache = []
    for msg in plan:
        cmd = msg.command
        if cmd == "open_run":
            output.append("{:=^80}".format(" Open Run "))
        elif cmd == "close_run":
            output.append("{:=^80}".format(" Close Run "))
        elif cmd == "set":
            output.append(
                "{motor.name} -> {args[0]}".format(
                    motor=msg.obj, args=msg.args
                )
            )
        elif cmd == "create":
            pass
        elif cmd == "read":
            read_cache.append(msg.obj.name)
        elif cmd == "save":
            output.append("  Read {}".format(read_cache))
            read_cache = []
    return "\n".join(output)


def configure_area_det(det, exposure, acq_time):
    """Configure exposure time of a detector in continuous acquisition mode"""
    _check_mini_expo(exposure, acq_time)
    yield from bps.mv(det.cam.acquire_time, acq_time)
    res = yield from bps.read(det.cam.acquire_time)
    real_acq_time = res[det.cam.acquire_time.name]["value"] if res else 1
    if hasattr(det, "images_per_set"):
        # compute number of frames
        num_frame = np.ceil(exposure / real_acq_time)
        yield from bps.mv(det.images_per_set, num_frame)
    else:
        # The dexela detector does not support `images_per_set` so we just
        # use whatever the user asks for as the thing
        num_frame = 1
    computed_exposure = num_frame * real_acq_time

    # print exposure time
    print(
        "INFO: requested exposure time = {} - > computed exposure time"
        "= {}".format(exposure, computed_exposure)
    )
    return num_frame, real_acq_time, computed_exposure


def _configure_area_det(exposure):
    """private function to configure pe1c

    This binds the general public function to the xpdacq global state
    """
    det = xpd_configuration["area_det"]
    # cs studio configuration doesn't propagate to python level
    acq_time = glbl["frame_acq_time"]
    return configure_area_det(det, exposure, acq_time)


def _check_mini_expo(exposure, acq_time):
    if exposure < acq_time:
        raise ValueError(
            "WARNING: total exposure time: {}s is shorter "
            "than frame acquisition time {}s\n"
            "you have two choices:\n"
            "1) increase your exposure time to be at least"
            "larger than frame acquisition time\n"
            "2) increase the frame rate, if possible\n"
            "    - to increase exposure time, simply resubmit"
            " the ScanPlan with a longer exposure time\n"
            "    - to increase frame-rate/decrease the"
            " frame acquisition time, please use the"
            " following command:\n"
            "    >>> {} \n then rerun your ScanPlan definition"
            " or rerun the xrun.\n"
            "Note: by default, xpdAcq recommends running"
            "the detector at its fastest frame-rate\n"
            "(currently with a frame-acquisition time of"
            "0.1s)\n in which case you cannot set it to a"
            "lower value.".format(
                exposure,
                acq_time,
                ">>> glbl['frame_acq_time'] = 0.5  #set" " to 0.5s",
            )
        )


def shutter_step(detectors, motor, step):
    """ customized step to ensure shutter is open before
    reading at each motor point and close shutter after reading
    """
    yield from bps.checkpoint()
    yield from bps.abs_set(motor, step, wait=True)
    yield from open_shutter_stub()
    yield from bps.sleep(glbl["shutter_sleep"])
    yield from bps.trigger_and_read(list(detectors) + [motor])
    yield from close_shutter_stub()


def open_shutter_stub():
    """simple function to return a generator that yields messages to
    open the shutter"""
    yield from bps.abs_set(
        xpd_configuration["shutter"], XPD_SHUTTER_CONF["open"], wait=True
    )
    yield from bps.sleep(glbl["shutter_sleep"])
    yield from bps.checkpoint()


def close_shutter_stub():
    """simple function to return a generator that yields messages to
    close the shutter"""
    yield from bps.abs_set(
        xpd_configuration["shutter"], XPD_SHUTTER_CONF["close"], wait=True
    )
    yield from bps.checkpoint()


def ct(dets, exposure):
    """
    Take one reading from area detector with given exposure time

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to area detector
        linked to xpdAcq.
    exposure : float
        total time of exposrue in seconds

    Notes
    -----
    area detector being triggered will  always be the one configured
    in global state. To find out which these are, please using
    following commands:

        >>> xpd_configuration['area_det']

    to see which device is being linked
    """

    pe1c, = dets
    md = {}
    # setting up area_detector
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(
        exposure
    )
    area_det = xpd_configuration["area_det"]
    # update md
    _md = ChainMap(
        md,
        {
            "sp_time_per_frame": acq_time,
            "sp_num_frames": num_frame,
            "sp_requested_exposure": exposure,
            "sp_computed_exposure": computed_exposure,
            "sp_type": "ct",
            "sp_uid": str(uuid.uuid4()),
            "sp_plan_name": "ct",
        },
    )
    plan = bp.count([area_det], md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable([]))
    yield from plan


def Tramp(dets, exposure, Tstart, Tstop, Tstep, *, per_step=shutter_step):
    """
    Collect data over a range of temperatures

    This plan sets the sample temperature using a temp_controller device
    and exposes a detector for a set time at each temperature.
    It also has logic for equilibrating the temperature before each
    acquisition. By default it closes the fast shutter at XPD in between
    exposures. This behavior may be overridden, leaving the fast shutter
    open for the entire scan. Please see below.

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to the temperature
        controller and area detector linked to xpdAcq.
    exposure : float
        exposure time at each temperature step in seconds.
    Tstart : float
        starting point of temperature sequence.
    Tstop : float
        stoping point of temperature sequence.
    Tstep : float
        step size between Tstart and Tstop of this sequence.
    per_step : callable, optional
        hook for customizing action at each temperature point.
        Tramp uses this for opening and closing the shutter at each
        temperature acquisition.

        Default behavior:
        `` open shutter - collect data - close shutter ``

        To make shutter always open during the temperature ramp,
        pass ``None`` to this argument. See ``Notes`` below for more
        detailed information.

    Notes
    -----
    1. To see which area detector and temperature controller
    will be used, type the following commands:

        >>> xpd_configuration['area_det']
        >>> xpd_configuration['temp_controller']

    2. To change the default behavior to shutter-always-open,
    please pass the argument for ``per_step`` in the ``ScanPlan``
    definition, as follows:

        >>> ScanPlan(bt, Tramp, 5, 300, 250, 10, per_step=None)

    This will create a ``Tramp`` ScanPlan, with shutter always
    open during the ramping.
    """

    pe1c, = dets
    md = {}
    # setting up area_detector
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(
        exposure
    )
    area_det = xpd_configuration["area_det"]
    temp_controller = xpd_configuration["temp_controller"]
    # compute Nsteps
    (Nsteps, computed_step_size) = _nstep(Tstart, Tstop, Tstep)
    # update md
    _md = ChainMap(
        md,
        {
            "sp_time_per_frame": acq_time,
            "sp_num_frames": num_frame,
            "sp_requested_exposure": exposure,
            "sp_computed_exposure": computed_exposure,
            "sp_type": "Tramp",
            "sp_startingT": Tstart,
            "sp_endingT": Tstop,
            "sp_requested_Tstep": Tstep,
            "sp_computed_Tstep": computed_step_size,
            "sp_Nsteps": Nsteps,
            "sp_uid": str(uuid.uuid4()),
            "sp_plan_name": "Tramp",
        },
    )
    plan = bp.scan(
        [area_det],
        temp_controller,
        Tstart,
        Tstop,
        Nsteps,
        per_step=per_step,
        md=_md,
    )
    plan = bpp.subs_wrapper(plan, LiveTable([temp_controller]))
    yield from plan


def Tlist(dets, exposure, T_list, *, per_step=shutter_step):
    """
    Collect data over a list of user-specific temperatures

    This plan sets the sample temperature using a temp_controller device
    and exposes a detector for a set time at each temperature.
    It also has logic for equilibrating the temperature before each
    acquisition. By default it closes the fast shutter at XPD in between
    exposures. This behavior may be overridden, leaving the fast shutter
    open for the entire scan. Please see below.

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to the temperature
        controller and area detector linked to xpdAcq.
    exposure : float
        total time of exposure in seconds
    T_list : list
        a list of temperatures where a scan will be run
    per_step : callable, optional
        hook for customizing action at each temperature point.
        Tramp uses this for opening and closing the shutter at each
        temperature acquisition.

        Default behavior:
        `` open shutter - collect data - close shutter ``

        To make shutter always open during the temperature ramp,
        pass ``None`` to this argument. See ``Notes`` below for more
        detailed information.

    Notes
    -----
    1. To see which area detector and temperature controller
    will be used, type the following commands:

        >>> xpd_configuration['area_det']
        >>> xpd_configuration['temp_controller']

    2. To change the default behavior to shutter-always-open,
    please pass the argument for ``per_step`` in the ``ScanPlan``
    definition, as follows:

        >>> ScanPlan(bt, Tlist, 5, [300, 250, 198], per_step=None)

    This will create a ``Tlist`` ScanPlan, with shutter always
    open during the ramping.
    """

    pe1c, = dets
    # setting up area_detector and temp_controller
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(
        exposure
    )
    area_det = xpd_configuration["area_det"]
    T_controller = xpd_configuration["temp_controller"]
    xpdacq_md = {
        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_requested_exposure": exposure,
        "sp_computed_exposure": computed_exposure,
        "sp_T_list": T_list,
        "sp_type": "Tlist",
        "sp_uid": str(uuid.uuid4()),
        "sp_plan_name": "Tlist",
    }
    # pass xpdacq_md to as additional md to bluesky plan
    plan = bp.list_scan(
        [area_det], T_controller, T_list, per_step=per_step, md=xpdacq_md
    )
    plan = bpp.subs_wrapper(plan, LiveTable([T_controller]))
    yield from plan


def tseries(dets, exposure, delay, num, auto_shutter=True):
    """
    time series scan with area detector.

    Parameters
    ----------
    dets : list
        list of 'readable' objects. default to area detector
        linked to xpdAcq.
    exposure : float
        exposure time at each reading from area detector in seconds
    delay : float
        delay between two consecutive readings from area detector in seconds
    num : int
        total number of readings
    auto_shutter: bool, optional
        Option on whether delegates shutter control to ``xpdAcq``. If True,
        following behavior will take place:

        `` open shutter - collect data - close shutter ``

        To make shutter stay open during ``tseries`` scan,
        pass ``False`` to this argument. See ``Notes`` below for more
        detailed information.

    Notes
    -----
    To see which area detector and shutter will be used, type the
    following commands:

        >>> xpd_configuration['area_det']
        >>> xpd_configuration['shutter']

    To override default behavior and keep the shutter open throughout
    scan , create ScanPlan with following syntax:

        >>> ScanPlan(bt, tseries, 10, 5, 10, False)
    """

    pe1c, = dets
    md = {}
    # setting up area_detector
    area_det = xpd_configuration["area_det"]
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(
        exposure
    )
    real_delay = max(0, delay - computed_exposure)
    period = max(computed_exposure, real_delay + computed_exposure)
    print(
        "INFO: requested delay = {}s  -> computed delay = {}s".format(
            delay, real_delay
        )
    )
    print(
        "INFO: nominal period (neglecting readout overheads) of {} s".format(
            period
        )
    )
    # update md
    _md = ChainMap(
        md,
        {
            "sp_time_per_frame": acq_time,
            "sp_num_frames": num_frame,
            "sp_requested_exposure": exposure,
            "sp_computed_exposure": computed_exposure,
            "sp_requested_delay": delay,
            "sp_requested_num": num,
            "sp_type": "tseries",
            # need a name that shows all parameters values
            # 'sp_name': 'tseries_<exposure_time>',
            "sp_uid": str(uuid.uuid4()),
            "sp_plan_name": "tseries",
        },
    )
    plan = bp.count([area_det], num, delay, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable([]))

    def inner_shutter_control(msg):
        if msg.command == "trigger":

            def inner():
                yield from open_shutter_stub()
                yield msg

            return inner(), None
        elif msg.command == "save":
            return None, close_shutter_stub()
        else:
            return None, None

    if auto_shutter:
        plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan


def _nstep(start, stop, step_size):
    """ helper function to compute number of steps and step_size
    """
    requested_nsteps = abs((start - stop) / step_size)

    computed_nsteps = int(requested_nsteps) + 1  # round down for a finer step
    computed_step_list = np.linspace(start, stop, computed_nsteps)
    computed_step_size = computed_step_list[1] - computed_step_list[0]
    print(
        "INFO: requested temperature step size = {} ->"
        "computed temperature step size = {}".format(
            step_size, computed_step_size
        )
    )
    return computed_nsteps, computed_step_size


# stream_name='primary'

register_plan("ct", ct)
register_plan("Tramp", Tramp)
register_plan("tseries", tseries)
register_plan("Tlist", Tlist)


# register_plan('statTramp', statTramp)


def new_short_uid():
    return str(uuid.uuid4())[:8]


def _clean_info(obj):
    """ stringtify and replace space"""
    return str(obj).strip().replace(" ", "_")


class MDOrderedDict(OrderedDict):
    """The augmented ordered dictionary."""

    def sel(self, ind: int):
        """Select the value by the index."""
        try:
            return list(self.values())[ind]
        except IndexError:
            raise IndexError("Index out of range.")

    def get_md(self, ind: int):
        """special method to get metadata of sample object based on
        bt.list index
        """
        obj_list = list(self.values())
        md_dict = dict(obj_list[ind])
        return md_dict


class Beamtime(ValidatedDictLike, YamlDict, ABC):
    """
    class that carries necessary information for a beamtime

    Parameters
    ----------
    pi_last : str
        last name of PI to this beamtime.
    saf_num : int
        Safty Approval Form number to current beamtime.
    experimenters : list, optional
        list of experimenter names. Each of experimenter name is
        expected to be comma separated as `first_name', `last_name`.
    wavelength : float, optional
        wavelength of current beamtime, in angstrom.
    kwargs :
        extra keyword arguments for current beamtime.

    Examples
    --------
    Inspect avaiable samples, plans.
    >>> print(bt)
    ScanPlans:
    0: (...summary of scanplan...)

    Samples:
    0: (...name of sample...)

    or equivalently
    >>> bt.list()
    ScanPlans:
    0: (...summary of scanplan...)

    Samples:
    0: (...name of sample...)
    """

    _REQUIRED_FIELDS = ["bt_piLast", "bt_safN"]

    def __init__(
        self, pi_last, saf_num, experimenters=None, *, wavelength=None, **kwargs
    ):
        if experimenters is None:
            experimenters = []
        super().__init__(
            bt_piLast=_clean_info(pi_last),
            bt_safN=_clean_info(saf_num),
            bt_experimenters=experimenters,
            bt_wavelength=wavelength,
            **kwargs
        )
        self._wavelength = wavelength
        self.scanplans = MDOrderedDict()
        self.samples = MDOrderedDict()
        self._referenced_by = []
        # used by YamlDict when reload
        self.setdefault("bt_uid", new_short_uid())
        self.robot_info = {}
        self._scanplan_order = {}
        self._sample_order = {}

    @property
    def wavelength(self):
        """ wavelength value of current beamtime. updated value will be
        passed down to all related objects"""
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val):
        self._wavelength = val
        self.update(bt_wavelength=val)

    @property
    def md(self):
        """ metadata of current object """
        return dict(self)

    @property
    def all_sample_in_magazine(self):
        """All samples in the robot magazine"""
        return [
            i
            for i, (k, v) in enumerate(self.samples.items())
            if v["sa_uid"] in self.robot_info
        ]

    def validate(self):
        # This is automatically called whenever the contents are changed.
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl["yaml_dir"], "bt_bt.yml").format(**self)

    def register_scanplan(self, scanplan):
        # Notify this Beamtime about an ScanPlan that should be re-synced
        # whenever the contents of the Beamtime are edited.
        scanplan_name = scanplan.short_summary()
        self.scanplans.update({scanplan_name: scanplan})
        # yaml sync list
        self._referenced_by.append(scanplan)
        # save order
        with open(
            os.path.join(glbl["config_base"], ".scanplan_order.yml"), "w+"
        ) as f:
            scanplan_order = {}
            for i, name in enumerate(self.scanplans.keys()):
                scanplan_order.update({i: name + ".yml"})
            # debug line
            self._scanplan_order = scanplan_order
            yaml.dump(scanplan_order, f)

    def register_sample(self, sample):
        # Notify this Beamtime about an Sample that should be re-synced
        # whenever the contents of the Beamtime are edited.
        sample_name = sample.get("sample_name", None)
        self.samples.update({sample_name: sample})
        # yaml sync list
        self._referenced_by.append(sample)
        # save order
        with open(
            os.path.join(glbl["config_base"], ".sample_order.yml"), "w+"
        ) as f:
            sample_order = {}
            for i, name in enumerate(self.samples.keys()):
                sample_order.update({i: name + ".yml"})
            # debug line
            self._sample_order = sample_order
            yaml.dump(sample_order, f)

    @classmethod
    def from_yaml(cls, f):
        d = yaml.unsafe_load(f)
        instance = cls.from_dict(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dict(cls, d):
        return cls(
            d.pop("bt_piLast"),
            d.pop("bt_safN"),
            d.pop("bt_experimenters"),
            wavelength=d.pop("bt_wavelength"),
            bt_uid=d.pop("bt_uid"),
            **d
        )

    def __str__(self):
        contents = [
            "", "ScanPlans:"
        ]
        contents.extend(
            [
                "{}: {}".format(i, sp_name)
                for i, sp_name in enumerate(self.scanplans.keys())
            ]
        )
        contents.extend(
            ["", "Samples:"]
        )
        contents.extend(
            [
                "{}: {}".format(i, sa_name)
                for i, sa_name in enumerate(self.samples.keys())
            ]
        )
        return "\n".join(contents)

    def list(self):
        """ method to list out all ScanPlan and Sample objects related
        to this Beamtime object
        """
        # for back-compat
        print(self)

    def list_bkg(self):
        """ method to list background object only """

        contents = ["", "Background:"] + [
            "{}: {}".format(i, sa_name)
            for i, sa_name in enumerate(self.samples.keys())
            if sa_name.startswith("bkgd")
        ]
        print("\n".join(contents))

    def robot_location_number(self, geometry=None):
        """Add information about the samples so that they can be loaded by the
        robot

        Parameters
        ----------
        geometry : {'capillary', 'plate', None}, optional
            The geometry of the samples to be loaded, if None use the capillary
            geometry. Defaults to None

        """
        print(
            "Please input the location of each sample in the robot"
            "magazine. If the sample is not in the magazine just leave it "
            "blank and hit <enter>."
        )
        for i, sample in enumerate(self.samples.keys()):
            print(i, sample)
            ip = input()
            if ip:
                loc = int(ip)
                self.robot_info[self.samples[sample]["sa_uid"]] = {
                    "robot_identifier": loc,
                    "robot_geometry": geometry,
                }

    def _robot_barcode_number(self):
        # PROTOTYPE!!!
        # while True:
        # ask for user input
        # ask for QR from reader
        # if done brake
        raise NotImplementedError("This is currently not implemented")

    def _robot_barcode_barcode(self):
        # PROTOTYPE!!!
        # Read from barcode reader
        # split into base and sample via mod 2
        qrs = []
        locs, sample_barcode = qrs[::2], qrs[1::2]
        for loc, sb in zip(locs, sample_barcode):
            self.robot_info[sb] = {"robot_identifer": loc}
        raise NotImplementedError("This is currently not implemented")


class Sample(ValidatedDictLike, YamlChainMap, ABC):
    """
    class that carries sample-related metadata

    after creation, this Sample object will be related to Beamtime
    object given as argument and will be available in bt.list()

    Parameters
    ----------
    beamtime : xpdacq.beamtime.Beamtime
        object representing current beamtime
    sample_md : dict
        dictionary contains all sample related metadata
    kwargs :
        keyword arguments for extr metadata

    Examples
    --------
    >>> Sample(bt, {'sample_name': 'Ni', 'sample_composition':{'Ni': 1}})

    >>> Sample(bt, {'sample_name': 'TiO2',
                    'sample_composition':{'Ti': 1, 'O': 2}})

    Please refer to http://xpdacq.github.io for more examples.
    """

    _REQUIRED_FIELDS = ["sample_name"]

    def __init__(self, beamtime: Beamtime, sample_md: dict):
        if ('sample_name' not in sample_md) and ('sample_composition' not in sample_md):
            raise ValueError(
                "At least sample_name and sample_composition is needed.\n"
                "For example\n"
                ">>> sample_md = {'sample_name':'Ni',"
                "'sample_composition':{'Ni':1}}\n"
                ">>> Sample(bt, sample_md)\n"
            )
        sample_md = regularize_dict_key(sample_md, ".", ",")
        super().__init__(sample_md, beamtime)  # ChainMap signature
        self.setdefault("sa_uid", new_short_uid())
        beamtime.register_sample(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(
            glbl["yaml_dir"], "samples", "{sample_name}.yml"
        ).format(**self)

    @classmethod
    def from_yaml(cls, f, beamtime=None):
        map1, map2 = yaml.unsafe_load(f)
        instance = cls.from_dicts(map1, map2, beamtime=beamtime)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dicts(cls, map1, map2, beamtime=None):
        if beamtime is None:
            beamtime = Beamtime.from_dict(map2)
        return cls(beamtime, map1)


class ScanPlan(ValidatedDictLike, YamlChainMap, ABC):
    """
    class that carries scan plan with corresponding experimental arguements

    after creation, this Sample object will be related to Beamtime
    object given as argument and will be available in bt.list()

    Parameters
    ----------
    beamtime : xpdacq.beamtime.Beamtime
        object representing current beamtime.
    plan_func :
        predefined plan function. For complete list of available functions,
        please refere to http://xpdacq.github.io for more information.
    args :
        positional arguments corresponding to plan function in used.
    kwargs :
        keyword arguments corresponding to plan function in used.

    Examples
    --------
    A `ct` (count) scan with 5s exposure time linked to Beamtime object `bt`.
    >>> ScanPlan(bt, ct, 5)

    `ScanPlan` class also takes keyword arguments.
    >>> ScanPlan(bt, ct, exposure=5)

    Please refer to http://xpdacq.github.io for more examples.
    """

    def __init__(self, beamtime, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        plan_name = plan_func.__name__
        sp_dict = {
            "sp_plan_name": plan_name,
            "sp_args": args,
            "sp_kwargs": kwargs,
        }
        if "sp_uid" in sp_dict["sp_kwargs"]:
            scanplan_uid = sp_dict["sp_kwargs"].pop("sp_uid")
            sp_dict.update({"sp_uid": scanplan_uid})
        # test if that is a valid plan
        exposure = kwargs.get("exposure")  # input as kwargs
        if exposure is None:
            # input as args
            exposure, *rest = args  # predefined scan signature
        _check_mini_expo(exposure, glbl["frame_acq_time"])
        super().__init__(sp_dict, beamtime)  # ChainMap signature
        self.setdefault("sp_uid", new_short_uid())
        self._bt = beamtime
        beamtime.register_scanplan(self)

    @property
    def md(self):
        """ metadata for current object """
        open_run, = [
            msg for msg in self.factory() if msg.command == "open_run"
        ]
        return open_run.kwargs

    @property
    def bound_arguments(self):
        """ bound arguments of this ScanPlan object """
        signature = inspect.signature(self.plan_func)
        # empty list is for [pe1c]
        bound_arguments = signature.bind(
            [], *self["sp_args"], **self["sp_kwargs"]
        )
        # bound_arguments.apply_defaults() # only valid in py 3.5
        complete_kwargs = bound_arguments.arguments
        # remove place holder for "dets"
        complete_kwargs.pop("dets")
        # replace callable objects, with its func name
        for k, v in complete_kwargs.items():
            if callable(v):
                complete_kwargs[k] = v.__name__
        return complete_kwargs

    def factory(self):
        # grab the area detector used in current configuration
        pe1c = xpd_configuration["area_det"]
        extra_kw = {}
        # pass parameter to plan_func -> needed for statTramp-like plan
        if "bt" in inspect.signature(self.plan_func).parameters:
            extra_kw["bt"] = self._bt
        plan = self.plan_func(
            [pe1c], *self["sp_args"], **self["sp_kwargs"], **extra_kw
        )
        return plan

    def short_summary(self):
        arg_value_str = list(map(str, self.bound_arguments.values()))
        fn = "_".join([self["sp_plan_name"]] + arg_value_str)
        return fn

    def __str__(self):
        return _summarize(self.factory())

    def __eq__(self, other):
        return self.to_yaml() == other.to_yaml()

    @classmethod
    def from_yaml(cls, f, beamtime=None):
        map1, map2 = yaml.unsafe_load(f)
        instance = cls.from_dicts(map1, map2, beamtime=beamtime)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dicts(cls, map1, map2, beamtime=None):
        if beamtime is None:
            beamtime = Beamtime.from_dict(map2)
        plan_name = map1.pop("sp_plan_name")
        plan_func = _PLAN_REGISTRY[plan_name]
        plan_uid = map1.pop("sp_uid")
        sp_args = map1["sp_args"]
        sp_kwargs = map1["sp_kwargs"]
        sp_kwargs.update({"sp_uid": plan_uid})
        return cls(beamtime, plan_func, *sp_args, **sp_kwargs)

    def default_yaml_path(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = "_".join([self["sp_plan_name"]] + list(arg_value_str))
        return os.path.join(glbl["yaml_dir"], "scanplans", "%s.yml" % fn)


def load_calibration_md(poni_file: str) -> dict:
    """Load the calibration metadata in a dictionary from a .poni file.

    Parameters
    ----------
    poni_file :
        The path to the .poni file.

    Returns
    -------
    calibration_md :
        The metadata in a dictionary.
    """
    ai = pyFAI.load(poni_file)
    return dict(ai.getPyFAI())


def count_with_calib(detectors: list, num: int = 1, delay: float = None, *, calibration_md: dict = None,
                     md: dict = None, test_mod: bool = False) -> typing.Generator:
    """
    Take one or more readings from detectors with shutter control and calibration metadata injection.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects

    num : integer, optional
        number of readings to take; default is 1

        If None, capture data until canceled

    delay : iterable or scalar, optional
        Time delay in seconds between successive readings; default is 0.

    calibration_md :
        The calibration data in a dictionary. If not applied, the function is a normal `bluesky.plans.count`.

    md : dict, optional
        metadata

    test_mod : bool
        Whether this is a run for the test functions.

    Notes
    -----
    If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
    the plan will raise a ``ValueError`` during iteration.
    """
    if not test_mod and glbl["auto_load_calib"]:
        raise PlanError(
            "Please set `glbl['auto_load_calib'] = False` before running this plan."
        )
    if md is None:
        md = dict()
    if calibration_md is not None:
        md["calibration_md"] = calibration_md

    def _per_shot(_detectors):
        yield from open_shutter_stub()
        yield from bps.one_shot(_detectors)
        yield from close_shutter_stub()
        return

    plan = bp.count(detectors, num, delay, md=md, per_shot=_per_shot)
    bpp.subs_wrapper(plan, LiveTable(detectors))
    sts = yield from plan
    return sts
