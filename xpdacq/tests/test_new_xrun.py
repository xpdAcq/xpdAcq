from pathlib import Path

import bluesky.plans as bp
import numpy as np
from databroker.v2 import Broker
from pkg_resources import resource_filename
from xpdacq.simulators import PerkinElmerDetector
from xpdacq.xpdacq import CustomizedRunEngine

PONI_FILE = resource_filename("xpdacq", "tests/Ni_poni_file.poni")


def test_force_use_poni_file(db: Broker, fresh_xrun: CustomizedRunEngine):
    xrun = fresh_xrun
    del fresh_xrun
    det = PerkinElmerDetector(name="pe1")
    xrun({}, bp.count([det]), poni_file=[(det, PONI_FILE)])
    assert hasattr(db[-1], "calib")


def test_use_mask_files(db: Broker, fresh_xrun: CustomizedRunEngine, tmp_path: Path):
    xrun = fresh_xrun
    del fresh_xrun
    det = PerkinElmerDetector(name="pe1")
    # make a mask
    mask = np.zeros((2, 2), dtype="int")
    mask_file = tmp_path.joinpath("mask.npy").absolute()
    np.save(mask_file, mask)
    xrun({}, bp.count([det]), mask_files=[(det, [mask_file])])
    assert hasattr(db[-1], "mask")
    _mask = db[-1].mask.read()["pe1_mask"].data[0]
    assert np.array_equal(mask, _mask)
