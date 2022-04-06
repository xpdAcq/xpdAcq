import typing as T

import bluesky.plan_stubs as bps
from bluesky import RunEngine
from bluesky_darkframes.sim import DiffractionDetector, Shutter
from databroker import Broker
from ophyd import Component, Device, Kind, Signal, SoftPositioner


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


class Camera(Device):

    acquire_time = Component(Signal, name="acquire_time", kind=Kind.config, value=0.1)


class PerkinElmerDetector(DiffractionDetector):

    cam = Component(Camera, name="cam")
    images_per_set = Component(Signal, name="images_per_set", kind=Kind.config, value=1)


class FastShutter(Shutter):

    pass


class Eurotherm(SoftPositioner):

    def __init__(self, *, egu='K', limits=None, source='computed', init_pos=300., **kwargs):
        super().__init__(egu=egu, limits=limits, source=source, init_pos=init_pos, **kwargs)


class Stage(Device):

    x = Component(SoftPositioner, egu="mm", init_pos=0.)
    y = Component(SoftPositioner, egu="mm", init_pos=0.)
    z = Component(SoftPositioner, egu="mm", init_pos=0.)


class FilterBank(Device):

    flt1 = Component(SoftPositioner, init_pos="In")
    flt2 = Component(SoftPositioner, init_pos="In")
    flt3 = Component(SoftPositioner, init_pos="In")
    flt4 = Component(SoftPositioner, init_pos="In")


class RingCurrent(SoftPositioner):

    def __init__(self, *, egu='mA', limits=None, source='computed', init_pos=400., **kwargs):
        super().__init__(egu=egu, limits=limits, source=source, init_pos=init_pos, **kwargs)


class WorkSpace:

    def __init__(self) -> None:

        self.RE: RunEngine = RunEngine()
        self.db: Broker = Broker.named("temp")
        self.RE.subscribe(self.db.insert)
        self.det: PerkinElmerDetector = PerkinElmerDetector(name="pe1")
        self.eurotherm: Eurotherm = Eurotherm(name="temperature")
        self.shutter: FastShutter = FastShutter(name="shutter")
