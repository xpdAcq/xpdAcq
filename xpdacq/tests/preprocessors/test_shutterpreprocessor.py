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
    plan = bps.trigger(detector)
    plan = spp(plan)
    steps = list(plan)
    assert len(steps) == 6
    assert steps[0].command == "set"
    assert steps[0].obj is shutter
    assert steps[0].args == ("open",)
    assert steps[1].command == "wait"
    assert steps[2].command == "sleep"
    assert steps[3].command == "trigger"
    assert steps[3].obj is detector
    assert steps[4].command == "set"
    assert steps[4].obj is shutter
    assert steps[4].args == ("closed",)
    assert steps[5].command == "wait"


def test_use_with_dark_preprocessor():
    shutter = get_shutter()
    detector = get_detector()
    spp = ShutterPreprocessor(
        detector=detector,
        open_shutter=get_open_shutter(shutter),
        close_shutter=get_close_shutter(shutter)
    )
    dpp = DarkPreprocessor(
        detector=detector,
        open_shutter=get_open_shutter(shutter),
        close_shutter=get_close_shutter(shutter)
    )
    plan = bps.trigger(detector, group=short_uid("light"))
    plan = spp(dpp(plan))
    steps = list(plan)
    assert len(steps) >= 6
    steps = steps[-6:]
    assert steps[0].command == "set"
    assert steps[0].obj is shutter
    assert steps[0].args == ("open",)
    assert steps[1].command == "wait"
    assert steps[2].command == "sleep"
    assert steps[3].command == "trigger"
    assert steps[3].obj is detector
    assert steps[4].command == "set"
    assert steps[4].obj is shutter
    assert steps[4].args == ("closed",)
    assert steps[5].command == "wait"


def test_disable():
    shutter = get_shutter()
    detector = get_detector()
    spp = ShutterPreprocessor(
        detector=detector,
        open_shutter=get_open_shutter(shutter),
        close_shutter=get_close_shutter(shutter)
    )
    spp.enable()
    spp.disable()
    plan = bps.trigger(detector)
    plan = spp(plan)
    steps = list(plan)
    assert len(steps) == 1
