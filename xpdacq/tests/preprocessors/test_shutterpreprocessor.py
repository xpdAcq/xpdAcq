import bluesky.plan_stubs as bps
from xpdacq.preprocessors.shutterpreprocessor import (ShutterConfig,
                                                      ShutterPreprocessor)
from bluesky_darkframes.sim import DiffractionDetector, Shutter


def test_call():
    shutter = Shutter(name="shutter")
    detector = DiffractionDetector(name="detector")
    spp = ShutterPreprocessor(
        detector=detector,
        shutter_config=ShutterConfig(shutter, "open", "closed")
    )
    plan = bps.trigger_and_read([detector])
    plan = spp(plan)
    msgs = list(plan)
    expected = [
        ("set", shutter),
        ("wait", None),
        ("trigger", detector),
        ("wait", None),
        ("set", shutter),
        ("wait", None)
    ]
    real = [(msg.command, msg.obj) for msg in msgs[:len(expected)]]
    assert real == expected


def test_repr():
    shutter = Shutter(name="shutter")
    detector = DiffractionDetector(name="detector")
    spp = ShutterPreprocessor(
        detector=detector,
        shutter_config=ShutterConfig(shutter, "open", "closed")
    )
    assert spp.__repr__() == "<ShutterPreprocessor for detector>"
