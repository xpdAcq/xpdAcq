import typing as T

from ophyd import Device, Signal
from ophyd import Component as Cpt
from bluesky import Msg
from pyFAI.geometry import Geometry
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp


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
    """

    def __init__(self, detector: Device) -> None:
        """The preprocessor to inject calibration data.

        Args:
            detector (Device): The detector to associate the calibration data with.
        """
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
