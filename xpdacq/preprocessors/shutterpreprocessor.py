import typing as T
from turtle import delay

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import Msg
from ophyd import Device

from .shutterconfig import ShutterConfig

Plan = T.Generator[Msg, T.Any, T.Any]

class ShutterPreprocessor:
    """The preprocessor to mutate the plan so that the shutter will be open before every non dark trigger of the detector and closed after the trigger finishes.

    This preprocessor must be used after the DarkPreprocessor. It won't open the shutter for the trigger to take the dark frame. It will open the shutter only for those triggers in non-dark groups.

    Parameters
    ----------
    detector : Device
        The detector to take light images.
    dark_group_prefix : str, optional
        The group of trigger for dark frame, by default 'bluesky-darkframes-trigger'
    shutter_config : ShutterConfig
        The configuration of the shutter states, by default, read `xpd_configuration` and `XPD_SHUTTER_CONF`.
    delay : float, optional
        The time to wait between the open of the shutter and the trigger of the detector, by default 0.
    """

    def __init__(
        self, 
        *,
        detector: Device,
        dark_group_prefix: str = 'bluesky-darkframes-trigger',
        shutter_config: T.Optional[ShutterConfig] = None,
        delay: float = 0.
        ) -> None:
        if shutter_config is None:
            shutter_config = self._get_default_shutter_control()
        self._detector = detector
        self._delay = delay
        self._dark_group_prefix = dark_group_prefix
        self._shutter_config = shutter_config
        self._disabled = False
        self._group = None
            
    @staticmethod
    def _get_default_shutter_control() -> ShutterConfig:
        from xpdacq.xpdacq_conf import xpd_configuration
        from xpdconf.conf import XPD_SHUTTER_CONF
        return ShutterConfig(
            xpd_configuration["shutter"],
            XPD_SHUTTER_CONF["open"],
            XPD_SHUTTER_CONF["close"]
        )

    def __call__(self, plan: Plan) -> Plan:
        if self._disabled:
            return plan
        shutter = self._shutter_config.shutter
        open_state = self._shutter_config.open_state
        close_state = self._shutter_config.close_state

        def _open_shutter_before(msg: Msg) -> Plan:
            curr_state = (yield from bps.rd(shutter))
            if curr_state != open_state:
                yield from bps.mv(shutter, open_state)
            if self._delay > 0.:
                yield from bps.sleep(delay)
            return (yield msg)

        def _close_shutter() -> Plan:
            curr_state = (yield from bps.rd(shutter))
            if curr_state != close_state:
                yield from bps.mv(shutter, close_state)
            return


        def _mutate(msg: Msg):
            # open the shutter before a non dark trigger
            group = msg.kwargs.get("group")
            not_dark = (group is not None) and (not group.startswith(self._dark_group_prefix))
            if (msg.command == "trigger") and (msg.obj is self._detector) and not_dark:
                # remember the group
                self._group = group
                return _open_shutter_before(msg), None
            if (msg.command == "wait") and (msg.kwargs.get("group") == self._group):
                return None, _close_shutter()
            return None, None

        return bpp.plan_mutator(plan, _mutate)

    def disable(self) -> None:
        """Enable the shutter control.
        """
        self._disabled = True
        return

    def enable(self) -> None:
        """Disable the shutter control.
        """
        self._disabled = False
        return
    