import typing as T
from dataclasses import dataclass

from ophyd import Signal


@dataclass
class ShutterConfig:
    """The Configuration of the shutter control.

    Attributes
    ----------
    shutter : Signal
        The ophyd object of shutter.
    open_state: Any
        The scalar value of the shutter position when it is open.
    close_state: Any
        The scalar value of the shutter position when it is closed.
    delay : float
        The delay time after shutter open or close in seconds, default 0.0.
    """

    shutter: Signal
    open_state: T.Any
    close_state: T.Any
    delay: float = 0.

    @classmethod
    def from_xpdacq(cls):
        """Use the setting from the global configuration of xpdAcq."""
        from xpdacq.xpdacq_conf import xpd_configuration
        from xpdconf.conf import XPD_SHUTTER_CONF
        return cls(
            xpd_configuration["shutter"],
            XPD_SHUTTER_CONF["open"],
            XPD_SHUTTER_CONF["close"],
            0.
        )
