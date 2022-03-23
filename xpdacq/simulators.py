import typing as T
from collections import namedtuple

import bluesky.plan_stubs as bps
from bluesky_darkframes.sim import DiffractionDetector, Shutter


def get_shutter(name="shutter") -> Shutter:
    return Shutter(name=name)


def get_open_shutter(shutter: Shutter) -> T.Callable:

    def open_shutter():
        return (yield from bps.mv(shutter, "open"))

    return open_shutter


def get_close_shutter(shutter: Shutter) -> T.Callable:

    def close_shutter():
        return (yield from bps.mv(shutter, "closed"))

    return close_shutter


def get_detector(name="detector") -> DiffractionDetector:
    return DiffractionDetector(name=name)
