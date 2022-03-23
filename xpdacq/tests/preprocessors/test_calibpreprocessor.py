from xpdacq.preprocessors.calibpreprocessor import CalibInfo, CalibPreprocessor, set_calib_info
from bluesky_darkframes.sim import DiffractionDetector
from pkg_resources import resource_filename
from pyFAI.geometry import Geometry
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.run_engine import RunEngine

PONI_FILE = str(resource_filename("xpdacq", "tests/Ni_poni_file.poni"))


def test_set():
    det = DiffractionDetector(name="pe1c")
    cp = CalibPreprocessor(det)
    geo = Geometry(
        wavelength=1.,
        dist=1., 
        poni1=0., 
        poni2=0., 
        rot1=0., 
        rot2=0., 
        rot3=0., 
        detector="Perkin detector"
        )
    cp.set(geo)
    # check loading
    assert cp._calib_info.wavelength.get() == 1.
    assert cp._calib_info.dist.get() == 1.
    assert cp._calib_info.poni1.get() == 0.
    assert cp._calib_info.poni2.get() == 0.
    assert cp._calib_info.rot1.get() == 0.
    assert cp._calib_info.rot2.get() == 0.
    assert cp._calib_info.rot3.value == 0.
    assert cp._calib_info.detector.get() == "Perkin detector"
    assert cp._calib_info.calibrated.get() == True


def test_load():
    det = DiffractionDetector(name="pe1c")
    cp = CalibPreprocessor(det)
    assert cp.read(PONI_FILE) is None


def test_call():
    det_name = "pe1c"
    det = DiffractionDetector(name=det_name)
    cp = CalibPreprocessor(det)
    plan = cp(bp.count([det]))
    RE = RunEngine()
    data = []
    RE.subscribe(
        lambda name, doc: data.append(doc["data"]), 
        name="event"
        )
    RE(plan)
    del RE, plan, det
    # check data
    assert len(data) == 1
    attrs = ("wavelength", "dist", "poni1", "poni2", "rot1", "rot2", "rot3", "detector", "calibrated")
    for attr in attrs:
        signal = getattr(cp._calib_info, attr)
        key = "{}_{}".format(det_name, attr)
        value = data[0].get(key)
        assert value == signal.get()


def test_disable_and_enable():
    det_name = "pe1c"
    det = DiffractionDetector(name=det_name)
    cp = CalibPreprocessor(det)
    # test disable
    cp.disable()
    msgs1 = list(bps.read(det))
    msgs2 = list(cp(bps.read(det)))
    assert msgs1 == msgs2
    del  msgs1, msgs2
    # test enable
    cp.enable()
    msgs1 = list(bps.read(det))
    msgs2 = list(cp(bps.read(det)))
    assert len(msgs1) == (len(msgs2) - 1)
    assert msgs1 == msgs2[:-1]


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
    calib_info = CalibInfo(name="calib_data")
    RE(set_calib_info(calib_info, geo))
    assert calib_info.wavelength.get() == geo.wavelength
    assert calib_info.dist.get() == geo.dist
    assert calib_info.poni1.get() == geo.poni1
    assert calib_info.poni2.get() == geo.poni2
    assert calib_info.rot1.get() == geo.rot1
    assert calib_info.rot2.get() == geo.rot2
    assert calib_info.rot3.value == geo.rot3
    assert calib_info.detector.get() == geo.detector.name
    assert calib_info.calibrated.get() == True
