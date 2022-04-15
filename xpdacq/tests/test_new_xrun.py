from pathlib import Path

import bluesky.plans as bp
import numpy as np
from databroker import Broker, Header
from pkg_resources import resource_filename
from xpdacq.preprocessors import CalibPreprocessor
from xpdacq.simulators import PerkinElmerDetector
from xpdacq.xpdacq import CustomizedRunEngine

PONI_FILE = resource_filename("xpdacq", "tests/Ni_poni_file.poni")


def test_force_use_poni_file(db: Broker, fresh_xrun: CustomizedRunEngine):
    xrun = fresh_xrun
    del fresh_xrun
    det = PerkinElmerDetector(name="pe1")
    xrun.calib_preprocessors.append(CalibPreprocessor(det))
    xrun({}, bp.count([det]), poni_file=PONI_FILE)
    assert "calib" in db[-1].stream_names


def test_use_mask_files(
    db: Broker,
    fresh_xrun: CustomizedRunEngine,
    tmp_path: Path
):
    xrun = fresh_xrun
    del fresh_xrun
    det = PerkinElmerDetector(name="pe1")
    # make a mask
    mask = np.zeros((2, 2), dtype="int")
    mask_file = tmp_path.joinpath("mask.npy").absolute()
    np.save(mask_file, mask)
    xrun({}, bp.count([det]), mask_files=[(det, [mask_file])])
    run: Header = db[-1]
    assert "mask" in run.stream_names
    _mask = next(run.data(det.name, stream_name="mask"))
    assert np.array_equal(mask, _mask)
