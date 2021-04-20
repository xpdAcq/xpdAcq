"""Wrappers for the ophyd devices."""
from ophyd import Device, Signal
from ophyd.device import Component as Cpt


class CalibrationData(Device):
    dist = Cpt(Signal, value=1., kind='config')
    poni1 = Cpt(Signal, value=0., kind='config')
    poni2 = Cpt(Signal, value=0., kind='config')
    rot1 = Cpt(Signal, value=0., kind='config')
    rot2 = Cpt(Signal, value=0., kind='config')
    rot3 = Cpt(Signal, value=0., kind='config')
    pixel1 = Cpt(Signal, value=0., kind='config')
    pixel2 = Cpt(Signal, value=0., kind='config')
    detector = Cpt(Signal, value="", kind='config')
    wavelength = Cpt(Signal, value=0., kind='config')
