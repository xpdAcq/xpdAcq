import os
import pytest
import shutil
import uuid
import numpy as np
from .conftest import xpd_pe1c, xpd_configuration
from xpdacq.xpdacq import update_experiment_hash_uid
from xpdacq.calib import (
    _collect_img,
    xpdAcqException,
    _sample_name_phase_info_configuration,
    run_calibration,
    Calibration
)
from pyFAI.calibrant import Calibrant, CALIBRANT_FACTORY
from pkg_resources import resource_filename as rs_fn


@pytest.mark.parametrize(
    "sample_name, phase_info, tag, exception",
    [
        (None, None, "calib", None),
        (None, "Ni", "calib", xpdAcqException),
        ("Ni", None, "calib", xpdAcqException),
    ],
)
def test_configure_sample_info_args(sample_name, phase_info, tag, exception):
    if exception is None:
        _sample_name_phase_info_configuration(sample_name, phase_info, tag)
    else:
        with pytest.raises(exception):
            _sample_name_phase_info_configuration(sample_name, phase_info, tag)


@pytest.mark.parametrize(
    "sample_name, phase_info, tag, sample_md",
    [
        (
            None,
            None,
            "calib",
            {
                "composition_string": "Ni1.0",
                "sample_composition": {"Ni": 1.0},
                "sample_name": "Ni_calib",
                "sample_phase": {"Ni": 1.0},
            },
        )
    ],
)
def test_configure_sample_info_md(sample_name, phase_info, tag, sample_md):
    parsed_sample_md = _sample_name_phase_info_configuration(
        sample_name, phase_info, tag
    )
    assert parsed_sample_md == sample_md


def test_calib_md(fresh_xrun, exp_hash_uid, glbl, db):
    xrun = fresh_xrun
    # calib run
    sample_md = _sample_name_phase_info_configuration(None, None, "calib")
    calibrant = os.path.join(glbl["usrAnalysis_dir"], "Ni24.D")
    detector = "perkin_elmer"
    _collect_img(
        5,
        True,
        sample_md,
        "calib",
        xrun,
        detector=detector,
        calibrant=calibrant,
    )
    calib_hdr = db[-1]
    assert "Ni_calib" == calib_hdr.start["sample_name"]
    assert detector == calib_hdr.start["detector"]
    calibrant_obj = Calibrant(calibrant)
    assert calibrant_obj.dSpacing == calib_hdr.start["dSpacing"]
    assert calib_hdr.start["is_calibration"] == True
    assert all(v == calib_hdr.start[k] for k, v in sample_md.items())
    server_uid = calib_hdr.start["detector_calibration_server_uid"]
    client_uid = calib_hdr.start["detector_calibration_client_uid"]
    assert server_uid == exp_hash_uid
    assert server_uid == client_uid
    # production run
    xrun(0, 0)
    hdr = db[-1]
    client_uid = hdr.start["detector_calibration_client_uid"]
    assert client_uid == exp_hash_uid
    assert "detector_calibration_server_uid" not in hdr.start
    # new uid
    new_hash = update_experiment_hash_uid()
    # production run first
    xrun(0, 0)
    hdr = db[-1]
    client_uid = hdr.start["detector_calibration_client_uid"]
    assert client_uid == new_hash
    assert "detector_calibration_server_uid" not in hdr.start
    # new calib run
    _collect_img(
        5,
        True,
        sample_md,
        "calib",
        xrun,
        detector=detector,
        calibrant=calibrant,
    )
    calib_hdr = db[-1]
    server_uid = calib_hdr.start["detector_calibration_server_uid"]
    client_uid = calib_hdr.start["detector_calibration_client_uid"]
    assert server_uid == new_hash
    assert server_uid == client_uid
    # md link
    calib_server_uid = calib_hdr.start["detector_calibration_server_uid"]
    hdr_client_uid = hdr.start["detector_calibration_client_uid"]
    assert calib_server_uid == hdr_client_uid


def test_load_calibrant(fresh_xrun, bt):
    xrun = fresh_xrun
    xrun.beamtime = bt
    # pyfai factory
    for k, calibrant_obj in CALIBRANT_FACTORY.items():
        # light weight callback
        def check_eq(name, doc):
            assert calibrant_obj.dSpacing == doc["dSpacing"]
            assert k == doc["sample_name"]

        t = xrun.subscribe(check_eq, "start")
        # execute
        run_calibration(calibrant=k, phase_info=k, RE_instance=xrun,
                        wait_for_cal=False)
        # clean
        xrun.unsubscribe(t)
    # invalid calibrant
    with pytest.raises(xpdAcqException):
        run_calibration(
            calibrant="pyFAI", phase_info="buggy", RE_instance=xrun
        )
    # filepath
    pytest_dir = rs_fn("xpdacq", "tests/")
    src = os.path.join(pytest_dir, "Ni24.D")
    dst_base = os.path.abspath(str(uuid.uuid4()))
    os.makedirs(dst_base)
    fn = str(uuid.uuid4())
    dst = os.path.join(dst_base, fn + ".D")
    shutil.copy(src, dst)
    c = Calibration(calibrant=dst)

    def check_eq(name, doc):
        assert c.calibrant.dSpacing == doc["dSpacing"]
        assert dst == doc["sample_name"]

    t = xrun.subscribe(check_eq, "start")
    # execute
    run_calibration(calibrant=dst, phase_info="buggy", RE_instance=xrun)
    # clean
    xrun.unsubscribe(t)
