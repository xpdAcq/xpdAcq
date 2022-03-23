import typing as T

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import Msg
from ophyd import Component as Cpt
from ophyd import Device, Signal
from pyFAI.geometry import Geometry


class CalibInfo(Device):
    """The information of calibration from pyFAI.
    """

    wavelength = Cpt(Signal, name="wavelength", value=1.)
    dist = Cpt(Signal, name="dist", value=1.)
    poni1 = Cpt(Signal, name="poni1", value=0.)
    poni2 = Cpt(Signal, name="poni2", value=0.)
    rot1 = Cpt(Signal, name="rot1", value=0.)
    rot2 = Cpt(Signal, name="rot2", value=0.)
    rot3 = Cpt(Signal, name="rot3", value=0.)
    detector = Cpt(Signal, name="detector", value="Perkin")
    calibrated = Cpt(Signal, name="calibrated", value=False)


class CalibPreprocessor:
    """The preprocessor to inject calibration data.

    The calibration data of the detector will be stored in the ophyd device `CalibInfo`. This device will be read after the detector is read. The calibration data will be in the same stream as the image of the detector. Be aware that this preprocessor should be used before the DarkPreprocessor to make sure the calibration data will not be injected into the dark stream.

    Parameters
    ----------
    detector : Device
        The detector to associate the calibration data with.
    """

    def __init__(self, detector: Device) -> None:
        self._detector: Device = detector
        self._calib_info: CalibInfo = CalibInfo(name=detector.name)
        self._disabled: bool = False

    def set(self, geo: Geometry) -> None:
        """Set the calibration information using the geometry object."""
        self._calib_info.wavelength.set(geo.wavelength)
        self._calib_info.dist.set(geo.dist)
        self._calib_info.poni1.set(geo.poni1)
        self._calib_info.poni2.set(geo.poni2)
        self._calib_info.rot1.set(geo.rot1)
        self._calib_info.rot2.set(geo.rot2)
        self._calib_info.rot3.set(geo.rot3)
        self._calib_info.detector.set(geo.detector.name)
        self._calib_info.calibrated.set(True)
        return

    @property
    def calib_info(self) -> CalibInfo:
        """The ophyd device that holds the calibration information."""
        return self._calib_info

    def read(self, poni_file: str) -> None:
        """Read the calibration information from the poni file."""
        geo = Geometry()
        geo.load(poni_file)
        self.set(geo)
        return

    def disable(self) -> None:
        """Disable the preprocessing. Do nothing to the plan when called."""
        self._disabled = True
        return

    def enable(self) -> None:
        """Enable the preprocessing. Mutate the plan when called."""
        self._disabled = False
        return

    def __call__(self, plan: T.Generator[Msg, T.Any, T.Any]) -> T.Generator[Msg, T.Any, T.Any]:
        """Mutate the plan. Read the calibration information data every time after the detector is read."""
        if self._disabled:
            return plan

        def _mutate(msg: Msg):
            if msg.command == "read" and msg.obj is self._detector:
                return None, bps.read(self._calib_info)
            return None, None

        return bpp.plan_mutator(plan, _mutate)


def set_calib_info(calib_info: CalibInfo, geo: Geometry) -> T.Generator[Msg, None, None]:
    return bpp.pchain(
        bps.abs_set(calib_info.wavelength, geo.wavelength),
        bps.abs_set(calib_info.dist, geo.dist),
        bps.abs_set(calib_info.poni1, geo.poni1),
        bps.abs_set(calib_info.poni2, geo.poni2),
        bps.abs_set(calib_info.rot1, geo.rot1),
        bps.abs_set(calib_info.rot2, geo.rot2),
        bps.abs_set(calib_info.rot3, geo.rot3),
        bps.abs_set(calib_info.detector, geo.detector.name),
        bps.abs_set(calib_info.calibrated, True)
    )
