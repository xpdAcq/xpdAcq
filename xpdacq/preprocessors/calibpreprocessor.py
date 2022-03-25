import typing as T
from pathlib import Path

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import Msg
from ophyd import Component as Cpt
from ophyd import Device, Signal
from pyFAI.geometry import Geometry

Plan = T.Generator[Msg, None, None]


class CalibPreprocessorError(Exception):
    pass


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


class CalibPreprocessor:
    """The preprocessor to inject calibration data.

    The calibration data of the detector will be stored in the ophyd device `CalibInfo`. This device will be read after the detector is read. The calibration data will be in the same stream as the image of the detector. Be aware that this preprocessor should be used before the DarkPreprocessor to make sure the calibration data will not be injected into the dark stream.

    Parameters
    ----------
    detector : Device
        The detector to associate the calibration data with.
    stream_name: str
        The name of the stream to add calibratino data, default `calib`.
    """

    def __init__(
        self,
        detector: Device,
        stream_name: str = "calib",
        dark_group_prefix: str = "bluesky-darkframes-trigger"
    ) -> None:
        self._detector: Device = detector
        self._calib_info: CalibInfo = CalibInfo(name=detector.name)
        self._disabled: bool = False
        self._stream_name = stream_name
        self._dark_group_prefix: str = dark_group_prefix

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
        return

    @property
    def calib_info(self) -> CalibInfo:
        """The ophyd device that holds the calibration information."""
        return self._calib_info

    # a read that return a device tuple
    def read(self, poni_file: str) -> None:
        """Read the calibration information from the poni file."""
        poni_path = Path(poni_file)
        if not poni_path.is_file():
            raise CalibPreprocessorError("'{}' doesn't exits.".format(poni_file))
        geo = Geometry()
        geo.load(str(poni_path))
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
        #TODO: record calib info in a cache (state tuple -> device tuple for the calibration info)
        #TODO: if cache is empty, do not anything
        #TODO: elif record in the cache, use that to set the calib info.
        #TODO: else use the lastest one
        if self._disabled:
            return plan

        def _read_calib_info(msg: Msg):
            yield from bps.trigger_and_read([self._calib_info], name=self._stream_name)
            return (yield msg)

        def _mutate(msg: Msg):
            group = msg.kwargs["group"] if ("group" in msg.kwargs) and msg.kwargs["group"] else ""
            if (
                msg.command == "trigger"
            ) and (
                    msg.obj is self._detector
                ) and (
                not group.startswith(self._dark_group_prefix)
            ):
                return _read_calib_info(msg), None
            return None, None

        return bpp.plan_mutator(plan, _mutate)

    def set_calib_info(self, geo: Geometry) -> Plan:
        """Set the cailbration information device by the calibrated geometry.

        Parameters
        ----------
        calib_info : CalibInfo
            The device to hold calibration data.
        geo : Geometry
            The geometry obtained from calibration.

        Returns
        -------
        Plan
            A blueksy plan (generator).
        """
        return bpp.pchain(
            bps.abs_set(self._calib_info.wavelength, geo.wavelength),
            bps.abs_set(self._calib_info.dist, geo.dist),
            bps.abs_set(self._calib_info.poni1, geo.poni1),
            bps.abs_set(self._calib_info.poni2, geo.poni2),
            bps.abs_set(self._calib_info.rot1, geo.rot1),
            bps.abs_set(self._calib_info.rot2, geo.rot2),
            bps.abs_set(self._calib_info.rot3, geo.rot3),
            bps.abs_set(self._calib_info.detector, geo.detector.name)
        )
