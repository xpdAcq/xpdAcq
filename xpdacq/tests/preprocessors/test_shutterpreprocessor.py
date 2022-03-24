import bluesky.plan_stubs as bps
from bluesky.utils import short_uid
from xpdacq.preprocessors.darkpreprocessor import DarkPreprocessor
from xpdacq.preprocessors.shutterpreprocessor import ShutterPreprocessor
from xpdacq.simulators import (get_close_shutter, get_detector,
                               get_open_shutter, get_shutter)


def test_call(capsys):
    shutter = get_shutter()
    detector = get_detector()
    spp = ShutterPreprocessor(
        detector=detector,
        open_shutter=get_open_shutter(shutter),
        close_shutter=get_close_shutter(shutter)
    )
    plan = bps.trigger_and_read([detector])
    plan = spp(plan)
    msgs = list(plan)
    real = [(msg.command, msg.obj) for msg in msgs[:6]]
    expected = [
        ("set", shutter), 
        ("wait", None),
        ("trigger", detector),
        ("wait", None),
        ("set", shutter),
        ("wait", None)
    ]
    assert real == expected
