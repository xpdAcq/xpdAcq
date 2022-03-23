from bluesky.simulators import summarize_plan
from xpdacq.factories.shuttercontrolfactory import ShutterControlFactory
from xpdacq.simulators import get_close_shutter, get_open_shutter, get_shutter, get_detector


def test_get_take_reading(capsys):
    shutter = get_shutter()
    scf = ShutterControlFactory(
        open_shutter=get_open_shutter(shutter),
        close_shutter=get_close_shutter(shutter)
    )
    detector = get_detector()
    take_reading = scf.get_take_reading()
    summarize_plan(take_reading([detector]))
    captured = capsys.readouterr()
    assert captured.out == "shutter -> open\n  Read ['detector']\nshutter -> closed\n"
