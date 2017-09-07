import os
import pytest
import shutil
import numpy as np
from xpdacq.xpdacq import update_experiment_hash_uid
from xpdacq.calib import (_collect_img, xpdAcqException,
                          _sample_name_phase_info_configuration,
                          run_mask_builder)
from xpdan.tools import compress_mask
from pyFAI.calibrant import Calibrant
from pkg_resources import resource_filename as rs_fn


@pytest.mark.parametrize('sample_name, phase_info, tag, exception',
                         [(None, None, 'calib', None),
                          (None, None, 'mask', None),
                          (None, 'Ni', 'calib', xpdAcqException),
                          ('Ni', None, 'calib', xpdAcqException),
                          ('kapton', None, 'mask', xpdAcqException),
                          (None, 'C12H12N2O', 'mask', xpdAcqException),
                          ]
                         )
def test_configure_sample_info_args(sample_name, phase_info, tag, exception):
        if exception is None:
            _sample_name_phase_info_configuration(sample_name,
                                                  phase_info, tag)
        else:
            with pytest.raises(exception):
                _sample_name_phase_info_configuration(sample_name,
                                                      phase_info, tag)


@pytest.mark.parametrize('sample_name, phase_info, tag, sample_md',
                         [(None, None, 'calib',
                           {'composition_string': 'Ni1.0',
                            'sample_composition': {'Ni': 1.0},
                            'sample_name': 'Ni_calib',
                            'sample_phase': {'Ni': 1.0}}),
                          (None, None, 'mask',
                           {'composition_string': 'C12.0H12.0N2.0O1.0',
                            'sample_composition': {'C': 12.0, 'H': 12.0,
                                                   'N': 2.0, 'O': 1.0},
                            'sample_name': 'kapton',
                            'sample_phase': {'C12H12N2O': 1.0}})
                          ]
                         )
def test_configure_sample_info_md(sample_name, phase_info, tag, sample_md):
    parsed_sample_md = _sample_name_phase_info_configuration(sample_name,
                                                             phase_info,
                                                             tag)
    assert parsed_sample_md == sample_md


def test_calib_md(fresh_xrun, exp_hash_uid, glbl, db):
    xrun = fresh_xrun
    # calib run
    sample_md = _sample_name_phase_info_configuration(None, None, 'calib')
    calibrant = os.path.join(glbl['usrAnalysis_dir'], 'Ni24.D')
    detector = 'perkin_elmer'
    img, fn_template = _collect_img(5, True, sample_md, 'calib', xrun,
                                    detector=detector,
                                    calibrant=calibrant)
    assert img.shape == (5, 5)
    calib_hdr = db[-1]
    assert 'Ni_calib' == calib_hdr.start['sample_name']
    assert detector == calib_hdr.start['detector']
    calibrant_obj = Calibrant(calibrant)
    assert calibrant_obj.dSpacing == calib_hdr.start['dSpacing']
    assert calib_hdr.start['is_calibration'] == True
    assert all(v == calib_hdr.start[k] for k, v in sample_md.items())
    server_uid = calib_hdr.start['detector_calibration_server_uid']
    client_uid = calib_hdr.start['detector_calibration_client_uid']
    assert server_uid == exp_hash_uid
    assert server_uid == client_uid
    # production run
    xrun(0, 0)
    hdr = db[-1]
    client_uid = hdr.start['detector_calibration_client_uid']
    assert client_uid == exp_hash_uid
    assert 'detector_calibration_server_uid' not in hdr.start
    # new uid
    new_hash = update_experiment_hash_uid()
    # production run first
    xrun(0, 0)
    hdr = db[-1]
    client_uid = hdr.start['detector_calibration_client_uid']
    assert client_uid == new_hash
    assert 'detector_calibration_server_uid' not in hdr.start
    # new calib run
    img, fn_template = _collect_img(5, True, sample_md, 'calib', xrun,
                                    detector=detector,
                                    calibrant=calibrant)
    assert img.shape == (5, 5)
    calib_hdr = db[-1]
    server_uid = calib_hdr.start['detector_calibration_server_uid']
    client_uid = calib_hdr.start['detector_calibration_client_uid']
    assert server_uid == new_hash
    assert server_uid == client_uid
    # md link
    calib_server_uid = calib_hdr.start['detector_calibration_server_uid']
    hdr_client_uid = hdr.start['detector_calibration_client_uid']
    assert calib_server_uid == hdr_client_uid


def test_mask_md(fresh_xrun, exp_hash_uid, glbl, db):
    xrun = fresh_xrun
    # grab calib information
    pytest_dir = rs_fn('xpdacq', 'tests/')
    src = os.path.join(pytest_dir, glbl['calib_config_name'])
    dst = os.path.join(glbl['config_base'], glbl['calib_config_name'])
    shutil.copyfile(src, dst)
    # build mask
    xrun = fresh_xrun
    run_mask_builder(RE_instance=xrun)
    sample_md = _sample_name_phase_info_configuration(None, None, 'mask')
    assert os.path.isfile(glbl['mask_path'])
    hdr = db[-1]
    assert hdr.start['is_mask'] == True
    assert all(v == hdr.start[k] for k, v in sample_md.items())
    assert hdr.start['mask_server_uid'] == exp_hash_uid
    assert hdr.start['mask_client_uid'] == hdr.start['mask_server_uid']
    # production run
    mask = np.load(glbl['mask_path'])
    reload_sparse_mask = compress_mask(mask)
    xrun(0, 0)
    hdr = db[-1]
    assert hdr.start['mask_client_uid'] == exp_hash_uid
    assert reload_sparse_mask == hdr.start['mask']
    # update hash uid
    new_hash = update_experiment_hash_uid()
    # production run first
    xrun(0, 0)
    hdr = db[-1]
    client_uid = hdr.start['mask_client_uid']
    assert client_uid == new_hash
    assert 'mask_server_uid' not in hdr.start
    # build new mask
    run_mask_builder(RE_instance=xrun)
    mask_hdr = db[-1]
    server_uid = mask_hdr.start['mask_server_uid']
    client_uid = mask_hdr.start['mask_client_uid']
    assert server_uid == new_hash
    assert server_uid == client_uid
    # md link
    mask_server_uid = mask_hdr.start['mask_server_uid']
    hdr_client_uid = hdr.start['mask_client_uid']
    assert mask_server_uid == hdr_client_uid
