import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.run_engine import RunEngine
from ophyd.sim import hw
from pkg_resources import resource_filename
import bluesky.preprocessors as bpp
from xpdacq.preprocessors.calibpreprocessor import CalibPreprocessor, CalibInfo
from databroker import Broker

PONI_FILE = str(resource_filename("xpdacq", "tests/Ni_poni_file.poni"))


def test_set():
    ci = CalibInfo(name="calib_info")
    calib_result = (1., 200., 1000., 1500., 0.1, 0.2, 0.3, "Perkin detector")
    sts = ci.set(calib_result)
    assert sts is not None
    # check if the signals are set correctly
    assert ci.wavelength.get() == calib_result[0]
    assert ci.dist.get() == calib_result[1]
    assert ci.poni1.get() == calib_result[2]
    assert ci.poni2.get() == calib_result[3]
    assert ci.rot1.get() == calib_result[4]
    assert ci.rot2.get() == calib_result[5]
    assert ci.rot3.get() == calib_result[6]
    assert ci.detector.get() == calib_result[7]


def test_preprocessor_usage():
    devices = hw()
    det = devices.det
    det_z = devices.motor
    cp = CalibPreprocessor(det, locked_signals=[det_z])
    db = Broker.named("temp")
    RE = RunEngine()
    RE.subscribe(db.insert)
    
    def simple_count():
        return cp(bp.count([det]))
    
    # case 1: no cache, no calib
    plan1 = simple_count()
    RE(plan1)
    assert not hasattr(db[-1], "calib")
    # add cache
    pos1 = 1.
    calib_result1 = (1., 1., 0., 0., 0., 0., 0., "Perkin detector")
    cp.add_calib_result([pos1], calib_result1)
    pos2 = 2.
    calib_result2 = (1., 2., 0., 0., 0., 0., 0., "Perkin detector")
    cp.add_calib_result([pos2], calib_result2)
    pos3 = 3.
    # case 2: state in cache, use corresponding calib result
    plan2 = bpp.pchain(bps.mv(det_z, pos1), simple_count())
    RE(plan2)
    run = db[-1]
    attrs = ("wavelength", "dist", "poni1", "poni2", "rot1", "rot2", "rot3", "detector")
    for i in range(len(attrs)):
        key = "{}_{}".format(det.name, attrs[i])
        data = list(run.data(key, stream_name="calib"))[0]
        assert data == calib_result1[i]
    # case 3: state not in cache, use latest calib result
    plan3 = bpp.pchain(bps.mv(det_z, pos3), simple_count())
    RE(plan3)
    run = db[-1]
    for i in range(len(attrs)):
        key = "{}_{}".format(det.name, attrs[i])
        data = list(run.data(key, stream_name="calib"))[0]
        assert data == calib_result2[i]


# TODO: simply test if the plan is changed or not
def test_disable_and_enable():
    pass
