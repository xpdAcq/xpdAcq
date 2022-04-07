import shutil
from pathlib import Path

import pytest
from pkg_resources import resource_filename
from xpdacq.calib2 import RunCalibration
from xpdacq.preprocessors import CalibPreprocessor
from xpdacq.simulators import WorkSpace

_PONI_FILE = Path(resource_filename("xpdacq", "tests/Ni_poni_file.poni"))


@pytest.fixture
def poni_file(tmp_path):
    fp = tmp_path.joinpath(_PONI_FILE.name)
    shutil.copy(str(_PONI_FILE), str(fp))
    return fp


def test_without_running_pyFAI(fresh_xrun, poni_file):
    xrun = fresh_xrun
    del fresh_xrun
    ws = WorkSpace()
    cpp = CalibPreprocessor(ws.det)
    xrun.calib_preprocessors.append(cpp)
    glbl = {
        "config_base": str(poni_file.parent),
        "calib_config_name": poni_file.name,
        "frame_acq_time": 0.1
    }
    run_calibration = RunCalibration(xrun, glbl)
    run_calibration(wait_for_cal=False)
    assert len(cpp._cache) == 1
