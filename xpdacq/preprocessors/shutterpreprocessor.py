import typing as T
from turtle import delay

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import Msg
from ophyd import Device

Plan = T.Generator[Msg, T.Any, T.Any]
ShutterControl = T.Callable[[], Plan]


class ShutterPreprocessor:
    """The preprocessor to mutate the plan so that the shutter will be open before every non dark trigger of the detector and closed after the trigger finishes.

    This preprocessor must be used after the DarkPreprocessor. It won't open the shutter for the trigger to take the dark frame. It will open the shutter only for those triggers in non-dark groups.

    Parameters
    ----------
    detector : Device
        The detector to take light images.
    dark_group_prefix : str, optional
        The group of trigger for dark frame, by default 'bluesky-darkframes-trigger'
    open_shutter : ShutterControl, optional
        The plan function to open the shutter, by default, using `xpdacq.beamtime.open_shutter_stub`.
    close_shutter : ShutterControl, optional
        The plan function to close the shutter, by default, using `xpdacq.beamtime.close_shutter_stub`.
    delay : float, optional
        The time to wait between the open of the shutter and the trigger of the detector, by default 0.
    """

    def __init__(
        self, 
        *,
        detector: Device,
        dark_group_prefix: str = 'bluesky-darkframes-trigger',
        open_shutter: ShutterControl = None,
        close_shutter: ShutterControl = None,
        delay: float = 0.
        ) -> None:
        if open_shutter is None:
            from xpdacq.beamtime import open_shutter_stub
            open_shutter = open_shutter_stub
            del open_shutter_stub
        if close_shutter is None:
            from xpdacq.beamtime import close_shutter_stub
            close_shutter = close_shutter_stub
            del close_shutter_stub
        self._detector = detector
        self._delay = delay
        self._open_shutter = open_shutter
        self._close_shutter = close_shutter
        self._dark_group_prefix = dark_group_prefix
        self._disabled = False

    def __call__(self, plan: Plan) -> Plan:
        if self._disabled:
            return plan
        
        def _open_shutter_before(msg: Msg) -> Plan:
            yield from self._open_shutter()
            yield from bps.sleep(delay)
            return (yield msg)

        def _mutate(msg: Msg):
            if (msg.command == "trigger") and (msg.obj is self._detector) and (not msg.kwargs.get("group", "").startswith(self._dark_group_prefix)):
                return _open_shutter_before(msg), self._close_shutter()
            return None, None

        return bpp.plan_mutator(plan, _mutate)

    def disable(self) -> None:
        self._disabled = True
        return

    def enable(self) -> None:
        self._disabled = False
        return
    