import bluesky.plan_stubs as bps
from xpdacq.preprocessors.shutterpreprocessor import (ShutterConfig,
                                                      ShutterPreprocessor)
from xpdacq.simulators import get_detector, get_shutter


def test_call(capsys):
    shutter = get_shutter()
    detector = get_detector()
    spp = ShutterPreprocessor(
        detector=detector,
        shutter_config=ShutterConfig(shutter, "open", "closed")
    )
    plan = bps.trigger_and_read([detector])
    plan = spp(plan)
    msgs = list(plan)
    expected = [
        ("read", shutter),
        ("set", shutter),
        ("wait", None),
        ("trigger", detector),
        ("wait", None),
        ("read", shutter),
        ("set", shutter),
        ("wait", None)
    ]
    real = [(msg.command, msg.obj) for msg in msgs[:len(expected)]]
    assert real == expected
