import typing as T
from dataclasses import dataclass

from ophyd import Signal


@dataclass
class ShutterConfig:

    shutter: Signal
    open_state: T.Any
    close_state: T.Any
