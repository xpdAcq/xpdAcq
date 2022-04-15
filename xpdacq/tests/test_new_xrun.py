import bluesky.plans as bp
from pkg_resources import resource_filename

from databroker import Broker
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.simulators import PerkinElmerDetector
from xpdacq.preprocessors import CalibPreprocessor

PONI_FILE = resource_filename("xpdacq", "tests/Ni_poni_file.poni")


def test_force_use_poni_file(db: Broker, fresh_xrun: CustomizedRunEngine):
    xrun = fresh_xrun
    del fresh_xrun
    det = PerkinElmerDetector(name="pe1")
    xrun.calib_preprocessors.append(CalibPreprocessor(det))
    xrun({}, bp.count([det]), poni_file=PONI_FILE)
    assert "calib" in db[-1].stream_names
