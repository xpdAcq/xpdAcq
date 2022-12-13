"""A plan and plan stubs factory designed for XPD experiment."""
import functools
import subprocess
import typing as tp
from pathlib import Path
from pprint import pprint
from typing import Any, Generator, Tuple, Union

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import numpy as np
import ophyd
import pyFAI
from bluesky.plan_stubs import mv, null
from bluesky.simulators import summarize_plan
from bluesky_darkframes import DarkFramePreprocessor, SnapshotDevice
from databroker.v1 import Broker, Header
from pkg_resources import resource_filename
from tifffile import TiffWriter

from xpdacq.beamtime import Beamtime, ScanPlan
from xpdacq.devices import CalibrationData


def kwargs_wrapper(func: tp.Callable, **kwargs) -> tp.Callable:
    """A wrapper to update default kwargs for a function."""

    @functools.wraps(func)
    def _func(*_args, **_kwargs):
        for k, v in kwargs.items():
            _kwargs.setdefault(k, v)
        return func(*_args, **_kwargs)

    return _func


def config_by_ai(cb: CalibrationData, ai: pyFAI.AzimuthalIntegrator) -> tp.Generator:
    """Configure the calibration data in an area detector using the AzimuthalIntegrator.

    Parameters
    ----------
    cb : CalibrationData
        The device that hold the calibration data.

    ai : AzimuthalIntegrator
        The pyFAI AzimuthalIntegrator

    Yields
    ------
    Msg : Msg
        The bluesky message.
    """
    return (
        yield from bps.configure(cb, {"dist": ai.dist, "poni1": ai.poni1, "poni2": ai.poni2, "rot1": ai.rot1,
                                      "rot2": ai.rot2, "rot3": ai.rot3, "detector": ai.detector.name,
                                      "wavelength": ai.wavelength, "pixel1": ai.pixel1, "pixel2": ai.pixel2})
    )


def _mean(lst: tp.Iterable) -> tp.Any:
    """Calculate mean."""
    iter_lst = iter(lst)
    total = next(iter_lst)
    count = 1
    for other in iter_lst:
        total += other
    return total / count


def run_pyfai_calib2(run: Header, data_key: str, output_dir: str = "xpdacq_calib",
                     file_prefix: str = r"{start[uid]}_", **kwargs) -> pyFAI.AzimuthalIntegrator:
    """Run the pyFAi calibration2 for a data entry in databroker."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    args = ["pyFAI-calib2"]
    # add wavelength
    if "w" not in kwargs and "wavelength" not in kwargs and "bt_wavelength" in run.start:
        kwargs["wavelength"] = run.start["bt_wavelength"]
    # add poni file
    poni_path = output_dir.joinpath(
        file_prefix.format(start=run.start, stop=run.stop) + "{}.poni".format(data_key))
    kwargs["poni"] = str(poni_path)
    # add kwargs to args
    for k, v in kwargs.items():
        if len(k) == 1:
            args.append("-{}".format(k))
        else:
            args.append("--{}".format(k))
        args.append(str(v))
    # write out the file
    tiff_path = output_dir.joinpath(
        file_prefix.format(start=run.start, stop=run.stop) + "{}.tiff".format(data_key))
    avg_img: np.ndarray = _mean(run.data(data_key))
    tw = TiffWriter(str(tiff_path))
    tw.write(avg_img)
    args.append(str(tiff_path))
    # run the pyFAI-calib2
    cp = subprocess.run(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if cp.returncode != 0:
        raise RuntimeError("Error in pyFAI-calib2:\n{}".format(cp.stderr.decode()))
    if not poni_path.is_file():
        raise FileNotFoundError(
            "No poni file {}. Did you change the file name when you save the poni file?".format(
                str(poni_path)))
    ai = pyFAI.load(str(poni_path))
    return ai


class XrayBasicPlans:
    """The basic plans for measurements."""

    def __init__(self, shutter: ophyd.Device, shutter_open: tp.Any, shutter_close: tp.Any, db: Broker):
        """Initiate the object.

        All the functions here are wrappers of the bluesky. For every exposure, what will happen is

            yield from mv(shutter, shutter_open)
            yield from trigger_and_read(devices)
            yield from mv(shutter, shutter_close)

        Parameters
        ----------
        shutter : Device
            The shutter.
        shutter_open : Any
            The state where the shutter is open.
        shutter_close : Any
            The state where the shutter is close.
        db :
            The database used to save calibration data.
        """
        self.shutter = shutter
        self.shutter_open = shutter_open
        self.shutter_close = shutter_close
        self.db = db
        self.one_shot = kwargs_wrapper(bps.one_shot, take_reading=self.take_reading)
        self.one_1d_step = kwargs_wrapper(bps.one_1d_step, take_reading=self.take_reading)
        self.one_nd_step = kwargs_wrapper(bps.one_nd_step, take_reading=self.take_reading)
        self.count = kwargs_wrapper(bp.count, per_shot=self.one_shot)
        self.scan = kwargs_wrapper(bp.scan, per_step=self.one_nd_step)
        self.rel_scan = kwargs_wrapper(bp.rel_scan, per_step=self.one_nd_step)
        self.list_scan = kwargs_wrapper(bp.list_scan, per_step=self.one_nd_step)
        self.rel_list_scan = kwargs_wrapper(bp.rel_list_scan, per_step=self.one_nd_step)
        self.log_scan = kwargs_wrapper(bp.log_scan, per_step=self.one_nd_step)
        self.rel_log_scan = kwargs_wrapper(bp.rel_log_scan, per_step=self.one_nd_step)
        self.grid_scan = kwargs_wrapper(bp.grid_scan, per_step=self.one_nd_step)
        self.rel_grid_scan = kwargs_wrapper(bp.rel_grid_scan, per_step=self.one_nd_step)
        self.scan_nd = kwargs_wrapper(bp.scan_nd, per_step=self.one_nd_step)
        self.spiral = kwargs_wrapper(bp.spiral, per_step=self.one_nd_step)
        self.spiral_fermat = kwargs_wrapper(bp.spiral_fermat, per_step=self.one_nd_step)
        self.spiral_square = kwargs_wrapper(bp.spiral_square, per_step=self.one_nd_step)
        self.rel_spiral = kwargs_wrapper(bp.rel_spiral, per_step=self.one_nd_step)
        self.rel_spiral_fermat = kwargs_wrapper(bp.rel_spiral_fermat, per_step=self.one_nd_step)
        self.rel_spiral_square = kwargs_wrapper(bp.rel_spiral_square, per_step=self.one_nd_step)

    @staticmethod
    def config_by_poni(calib_cpt: CalibrationData, poni_file: str):
        """Configure the CalibrationData using the info in a poni file.

        Parameters
        ----------
        calib_cpt : CalibrationData
            The CalibrationData component to be configured.
        poni_file : str
            The path to the poni file.

        Yields
        ------
        Msg : Msg
            The plan message.
        """
        ai = pyFAI.load(poni_file)
        return (yield from config_by_ai(calib_cpt, ai))

    def shutter_wrapper(self, plan: tp.Generator):
        """Open the shutter at the start and close the shutter at the end."""
        yield from bps.mv(self.shutter, self.shutter_open)
        sts = (yield from plan)
        yield from bps.mv(self.shutter, self.shutter_close)
        return sts

    def trigger_and_read(self, devices: tp.Iterable[ophyd.Device], name="primary"):
        """
        Trigger and read a list of detectors and bundle readings into one Event, like

            shutter open
            trigger and read devices
            shutter close

        Parameters
        ----------
        devices : iterable
            devices to trigger (if they have a trigger method) and then read
        name : string, optional
            event stream name, a convenient human-friendly identifier; default
            name is 'primary'

        Yields
        ------
        msg : Msg
            messages to 'trigger', 'wait' and 'read'
        """
        return (yield from self.shutter_wrapper(bps.trigger_and_read(devices, name=name)))

    def take_reading(self, devices: tp.Iterable[ophyd.Device]) -> tp.Generator:
        """
        Trigger and read a list of detectors and bundle readings into one Event, like

            shutter open
            trigger and read devices
            shutter close

        Parameters
        ----------
        devices : iterable
            devices to trigger (if they have a trigger method) and then read

        Yields
        ------
        msg : Msg
            messages to 'trigger', 'wait' and 'read'
        """
        return (yield from self.trigger_and_read(devices))

    def calibrate(self, detectors: tp.List[ophyd.Device], calib_cpts: tp.List[CalibrationData], *,
                  output_dir: str = "xpdacq_calib", config_det: bool = True, pyfai_kwargs=None, md=None):
        """Take one or more readings from detectors and inject calibration metadata. A wrapper of bluesky.plans.count.

        Parameters
        ----------
        detectors : list of devices
            A 'readable' objects
        calib_cpts : str
            The calibration components in the detectors.
        output_dir : str
            The directory where the tiff file and poni file will be saved.
        config_det : bool
            Whether to configure the area detector or not after the calibration is done.
        pyfai_kwargs : dict, optional
            The kwargs for the pyFAI-calib2. Default {"detector": "perkin_elmer", "calibrant": "data/Ni24.D"}.
        md : dict, optional
            metadata

        Notes
        -----
        If ``delay`` is an iterable, it must have at least ``num - 1`` entries or
        the plan will raise a ``ValueError`` during iteration.
        """
        if not md:
            md = {}
        if not pyfai_kwargs:
            pyfai_kwargs = {}
        pyfai_kwargs.setdefault("detector", "Perkin detector")
        pyfai_kwargs.setdefault("calibrant", resource_filename("xpdacq", "data/Ni24.D"))
        _md = {
            "is_calibration": True,
            "pyfai_kwargs": pyfai_kwargs
        }
        _md.update(md)
        yield from bp.count(detectors, per_shot=self.trigger_and_read, md=md)
        run = self.db[-1]
        geometries = []
        for detector in detectors:
            data_key = "{}_image".format(detector.name)
            ai = run_pyfai_calib2(run, data_key=data_key, output_dir=output_dir, **pyfai_kwargs)
            geometries.append(ai)
        if config_det:
            for cb, ai in zip(calib_cpts, geometries):
                yield from config_by_ai(cb, ai)
        return geometries

    def dark_plan(self, detector):
        """The plan to take dark."""
        # Restage to ensure that dark frames goes into a separate file.
        yield from bps.unstage(detector)
        yield from bps.stage(detector)
        yield from bps.mv(self.shutter, self.shutter_close)
        # The `group` parameter passed to trigger MUST start with
        # bluesky-darkframes-trigger.
        yield from bps.trigger(detector, group='bluesky-darkframes-trigger')
        yield from bps.wait('bluesky-darkframes-trigger')
        snapshot = SnapshotDevice(detector)
        yield from bps.mv(self.shutter, self.shutter_open)
        # Restage.
        yield from bps.unstage(detector)
        yield from bps.stage(detector)
        return snapshot

    def create_dark_frame_preprocessor(self, *, detector: ophyd.Device, max_age: float,
                                       locked_signals: tp.List[ophyd.Signal] = None, limit: int = None,
                                       stream_name: str = "dark"):
        """Create a dark frame preprocessor. Used in a way `dark_frame_preprocessor(plan)`.

        Specifically this adds a new Event stream, named 'dark' by default. It
        inserts one Event with a reading that contains a 'dark' frame. The same
        reading may be used across multiple runs, depending on the rules for when a
        dark frame is taken.

        Parameters
        ----------
        detector: Device
            The detector used to take dark image.
        max_age: float
            Time after which a fresh dark frame should be acquired
        locked_signals: Iterable, optional
            Any changes to these signals invalidate the current dark frame and
            prompt us to take a new one. Typical examples would be exposure time or
            gain, anything that changes the expected dark frame.
        limit: integer or None, optional
            Number of dark frames to cache. If None, do not limit.
        stream_name: string, optional
            Event stream name for dark frames. Default is 'dark'.
        """
        return DarkFramePreprocessor(dark_plan=self.dark_plan, detector=detector, max_age=max_age,
                                     locked_signals=locked_signals, limit=limit, stream_name=stream_name)


class MultiDistPlans(XrayBasicPlans):
    """The wrappers of bluesky plans for a measurement where the detector moves."""

    def __init__(self, shutter: ophyd.Device, shutter_open: tp.Any, shutter_close: tp.Any, db: Broker,
                 detector: CalibrationData, calib_cpt: CalibrationData, motor: ophyd.Device):
        """Create the object.

        For every measurement, the single exposure event will be

            for position, stream, geometry in zip(positions, streams, geometries):
                yield from mv(motor, position)
                yield from config_calib_by_ai(calib_cpt, geometry)
                yield from mv(shutter, shutter_open)
                yield from trigger_and_read(devices)
                yield from mv(shutter, shutter_close)

        Parameters
        ----------
        shutter : Device
            The shutter.
        shutter_open : Any
            The state where the shutter is open.
        shutter_close : Any
            The state where the shutter is close.
        db:
            The database to save calibration data.
        """
        self.detector = detector
        self.calib_cpt = calib_cpt
        self.motor = motor
        self.positions = []
        self.streams = []
        self.geometries = []
        super(MultiDistPlans, self).__init__(shutter, shutter_open, shutter_close, db=db)

    def calib_dist(self, position: tp.Any, stream: str, output_dir: str = "xpdacq_calib", pyfai_kwargs=None,
                   md=None):
        """Calibration the distance and add it to the plan."""
        yield from bps.mv(self.motor, position)
        ais = yield from self.calibrate([self.detector], [self.calib_cpt], config_det=False, output_dir=output_dir,
                                        pyfai_kwargs=pyfai_kwargs, md=md)
        self.add_dist(position, stream, ais[0])

    def add_dist(self, position: tp.Any, stream: str, geometry: pyFAI.AzimuthalIntegrator):
        """Add a pre-calibrated distance to the plan."""
        self.positions.append(position)
        self.streams.append(stream)
        self.geometries.append(geometry)

    def pop_dist(self, index: int) -> tuple:
        """Pop out a distance."""
        p = self.positions.pop(index)
        s = self.streams.pop(index)
        g = self.geometries.pop(index)
        return p, s, g

    def clear_dists(self):
        """Clear all the record of distance."""
        self.positions = []
        self.streams = []
        self.geometries = []

    def take_reading(self, devices: tp.List[ophyd.Device]) -> tp.Generator:
        """Take reading of devices."""
        for position, stream, geometry in zip(self.positions, self.streams, self.geometries):
            yield from bps.mv(self.motor, position)
            yield from config_by_ai(self.calib_cpt, geometry)
            yield from self.trigger_and_read(devices, name=stream)


class BeamtimeHelper:
    """
    A class helping to tackle with tasks related to samples on a rack during the beam time.
    Attributes
    ----------
    _bt
        The instance storing meta data of the sample and plan
    _pos_key
        The key for the position of samples. Default is the global variable POS_KEYS
    """

    def __init__(self, bt: Beamtime, positioners: Tuple[Any, Any],
                 pos_key: Tuple[str, str] = ("sample_x", "sample_y")):
        """
        Initiate the class instance.
        Parameters
        ----------
        bt
            The instance storing meta data of the sample and plan
        pos_key
            (Optional) The keys of the horizontal position and vertical position fields. Default POS_KEY
        """
        self._bt = bt
        self._positioners = positioners
        self._pos_key = pos_key

    def get_sample(self, sample: Union[int, str]) -> dict:
        """
        Get metadata of a sample.
        Parameters
        ----------
        sample
            The sample index or sample name key
        Returns
        -------
        sample_meta
            the meta data of a sample
        """
        if isinstance(sample, str):
            sample_cls = self._bt.samples[sample]
        elif isinstance(sample, int):
            sample_cls = list(self._bt.samples.values())[sample]
        else:
            raise ValueError(f"{sample} is not int or str. It is {type(sample)}.")
        sample_meta = dict(sample_cls.items())
        return sample_meta

    def print_sample(self, *samples: Union[int, str]):
        """
        Print the sample information.
        Parameters
        ----------
        samples
            The sample index or sample name key
        """
        for sample in samples:
            sample_meta = self.get_sample(sample)
            pprint(sample_meta)

    def get_plan(self, plan: Union[int, str]) -> Generator:
        """
        Get the plan (message generator).
        Parameters
        ----------
        plan
            The plan index or plan name key
        Returns
        -------
        plan_gen
            The plan message generator.
        """
        if isinstance(plan, str):
            plan_cls: ScanPlan = self._bt.scanplans[plan]
        elif isinstance(plan, int):
            plan_cls: ScanPlan = list(self._bt.scanplans.values())[plan]
        else:
            raise ValueError(f"{plan} is not int or str. It is {type(plan)}.")
        plan_gen = plan_cls.factory()
        return plan_gen

    def print_plan(self, *plans: Union[int, str]):
        """
        Print the plan information.
        Parameters
        ----------
        plans
            The plan index or plan name key
        """
        for plan in plans:
            plan_gen = self.get_plan(plan)
            summarize_plan(plan_gen)

    def aim_at_sample(self, sample):
        """
        A generator of message: move the sample to the beam spot according to sample position metadata.
        Parameters
        ----------
        sample
            The sample index or sample name key
        Examples
        --------
        Initiate a BeamtimeHelper.
        >>> bthelper = BeamtimeHelper(bt)
        Check the motors.
        >>> xpd_configuration["x_controller"]
        >>> xpd_configuration["y_controller"]
        Aim at the sample of index 0 in bt.
        >>> RE(bthelper.aim_at_sample(0))
        Aim at the sample "Ni" in bt.
        >>> RE(bthelper.aim_at_sample("Ni"))
        """
        posx_controller, posy_controller = self._positioners
        sample_meta = self.get_sample(sample)
        name = sample_meta.get("sample_name")
        print(f"INFO: Target sample {name}")
        pos_x_key, pos_y_key = self._pos_key
        pos_x = sample_meta.get(pos_x_key)
        pos_y = sample_meta.get(pos_y_key)
        if pos_x is None:
            print(f"Warning: No {pos_x_key} in sample {sample} -> Do nothing")
        else:
            print(f"INFO: Move to x = {pos_x}")
            yield from mv(posx_controller, float(pos_x))
        if pos_y is None:
            print(f"Warning: No {pos_y_key} in sample {sample} -> Do nothing")
        else:
            print(f"INFO: Move to y = {pos_y}")
            yield from mv(posy_controller, float(pos_y))
        yield from null()

    def do(self, sample: tp.Union[int, str], plan: tp.Generator) -> tp.Generator:
        """Generate a measurement plan for a sample.

        The steps are

            aim the beam at the sample
            conduct the plan with the sample metadata injected

        Parameters
        ----------
        sample :
            The index or name of the sample.

        plan :
            The generator of the bluesky plan.

        Yields
        ------
        Msg :
            The plan messages.
        """
        yield from self.aim_at_sample(sample)
        yield from bpp.inject_md_wrapper(plan, md=self.get_sample(sample))
        sts = yield from plan
        return sts
