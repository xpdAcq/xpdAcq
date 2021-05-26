"""Wrappers for the ophyd devices."""
from ophyd import Device, Signal
from ophyd import Kind
from ophyd.device import Component as Cpt


class CalibrationData(Device):
    """A device to hold pyFAI calibration data."""
    dist = Cpt(Signal, value=1., kind=Kind.config)
    poni1 = Cpt(Signal, value=0., kind=Kind.config)
    poni2 = Cpt(Signal, value=0., kind=Kind.config)
    rot1 = Cpt(Signal, value=0., kind=Kind.config)
    rot2 = Cpt(Signal, value=0., kind=Kind.config)
    rot3 = Cpt(Signal, value=0., kind=Kind.config)
    pixel1 = Cpt(Signal, value=0., kind=Kind.config)
    pixel2 = Cpt(Signal, value=0., kind=Kind.config)
    detector = Cpt(Signal, value="", kind=Kind.config)
    wavelength = Cpt(Signal, value=0., kind=Kind.config)
