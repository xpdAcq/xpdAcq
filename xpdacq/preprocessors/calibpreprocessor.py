from ast import Or
import typing as T
from pathlib import Path
from collections import OrderedDict
from frozendict import frozendict

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import Msg
from ophyd import Component as Cpt
from ophyd import Device, Signal
from ophyd.status import Status
from pyFAI.geometry import Geometry

Plan = T.Generator[Msg, None, None]
SignalList = T.List[Signal]
CalibResult = T.Tuple[float, float, float, float, float, float, float, str]
State = T.Dict[str, T.Hashable]


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

    def set(self, calib_result: CalibResult, *args, **kwargs) -> Status:
        # args and kwargs are just holders
        del args
        del kwargs
        # try to put the tuple and return the status
        sts = Status(self, timeout=60.)
        try:
            self.put(calib_result)
        except Exception as error:
            sts.set_exception(error)
        else:
            sts.set_finished()
        return sts


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
        locked_signals: SignalList = None,
        stream_name: str = "calib",
        dark_group_prefix: str = "bluesky-darkframes-trigger"
    ) -> None:
        if locked_signals is None:
            locked_signals = []
        self._detector: Device = detector
        self._calib_info: CalibInfo = CalibInfo(name=detector.name)
        self._disabled: bool = False
        self._locked_signals = locked_signals
        self._stream_name = stream_name
        self._dark_group_prefix: str = dark_group_prefix
        self._cache = OrderedDict()

    @property
    def calib_info(self) -> CalibInfo:
        """The ophyd device that holds the calibration information."""
        return self._calib_info

    @property
    def locked_signals(self) -> SignalList:
        return self._locked_signals

    @staticmethod
    def _read(poni_file: str) -> CalibResult:
        """Read the calibration information from the poni file."""
        poni_path = Path(poni_file)
        if not poni_path.is_file():
            raise CalibPreprocessorError("'{}' doesn't exits.".format(poni_file))
        geo = Geometry()
        geo.load(str(poni_path))
        calib_result = (geo.wavelength, geo.dist, geo.poni1, geo.poni2,
                        geo.rot1, geo.rot2, geo.rot3, geo.detector.name)
        return calib_result

    # TODO: add method to add cache
    def add_calib_result(self, state: State, calib_result: CalibResult) -> None:
        key = frozendict(state)
        self._cache[key] = calib_result
        return

    def load_calib_result(self, state: State, poni_file: str) -> None:
        calib_result = self._read(poni_file)
        self.add_calib_result(state, calib_result)
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
        # TODO: record calib info in a cache (state tuple -> device tuple for the calibration info)
        # TODO: if cache is empty, do not anything
        # TODO: elif record in the cache, use that to set the calib info.
        # TODO: else use the lastest one
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

    def clear(self) -> None:
        self._cache.clear()
        return
