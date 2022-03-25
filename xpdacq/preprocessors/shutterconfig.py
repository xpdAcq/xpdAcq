import typing as T
from dataclasses import dataclass
from typing_extensions import Self

from ophyd import Signal


@dataclass
class ShutterConfig:

    shutter: Signal
    open_state: T.Any
    close_state: T.Any

    @classmethod
    def from_xpdacq(cls):
        from xpdacq.xpdacq_conf import xpd_configuration
        from xpdconf.conf import XPD_SHUTTER_CONF
        return cls(
            xpd_configuration["shutter"],
            XPD_SHUTTER_CONF["open"],
            XPD_SHUTTER_CONF["close"]
        )
