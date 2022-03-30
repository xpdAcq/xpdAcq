import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.run_engine import RunEngine
from bluesky_darkframes.sim import DiffractionDetector
from pkg_resources import resource_filename
from pyFAI.geometry import Geometry
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


def test_load():
    det = DiffractionDetector(name="pe1c")
    cp = CalibPreprocessor(det)
    assert cp._read(PONI_FILE) is None


def test_call():
    det_name = "pe1c"
    det = DiffractionDetector(name=det_name)
    cp = CalibPreprocessor(det)
    plan = cp(bp.count([det]))
    db = Broker.named("temp")
    RE = RunEngine()
    RE.subscribe(db.insert)
    RE(plan)
    del RE, plan, det
    # should find all the calibration data in the output
    run = db[-1]
    attrs = ("wavelength", "dist", "poni1", "poni2", "rot1", "rot2", "rot3", "detector", "calibrated")
    for attr in attrs:
        signal = getattr(cp._calib_info, attr)
        key = "{}_{}".format(det_name, attr)
        data = list(run.data(key, stream_name="calib"))
        assert len(data) == 1
        assert data[0] == signal.get()


def test_disable_and_enable():
    det_name = "pe1c"
    det = DiffractionDetector(name=det_name)
    cp = CalibPreprocessor(det)
    # test disable
    cp.disable()
    msgs1 = list(cp(bps.trigger(det)))
    assert len(msgs1) == 1
    assert msgs1[0].command == "trigger"
    assert msgs1[0].obj is det
    # test enable
    cp.enable()
    msgs2 = list(cp(bps.trigger(det)))
    assert len(msgs2) > 1
    assert msgs2[-1].command == "trigger"
    assert msgs2[-1].obj is det


def test_set_calib_info_using_RE():
    RE = RunEngine()
    geo = Geometry(
        wavelength=0.16,
        dist=200.,
        poni1=1000.,
        poni2=1000.,
        rot1=0.1,
        rot2=-0.2,
        rot3=0.3,
        detector="Perkin detector"
    )
    det = DiffractionDetector(name="pe1c")
    cp = CalibPreprocessor(det)
    RE(cp.set_calib_info(geo))
    assert cp.calib_info.wavelength.get() == geo.wavelength
    assert cp.calib_info.dist.get() == geo.dist
    assert cp.calib_info.poni1.get() == geo.poni1
    assert cp.calib_info.poni2.get() == geo.poni2
    assert cp.calib_info.rot1.get() == geo.rot1
    assert cp.calib_info.rot2.get() == geo.rot2
    assert cp.calib_info.rot3.get() == geo.rot3
    assert cp.calib_info.detector.get() == geo.detector.name
