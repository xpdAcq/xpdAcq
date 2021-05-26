##############################################################################
#
# xpdan            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Christopher J. Wright
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import shutil

import databroker
import ophyd.sim as sim
import pytest
from pkg_resources import resource_filename as rs_fn
from xpdsim import (
    cs700,
    simple_pe1c,
    shctl1,
    ring_current,
    xpd_wavelength,
    fb
)

import xpdacq.devices as devices
from xpdacq.beamtimeSetup import _start_beamtime
from xpdacq.utils import import_sample_info
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.xpdacq_conf import glbl_dict, configure_device


@pytest.fixture(scope="session")
def db():
    db = databroker.v1.temp()
    return db


@pytest.fixture(scope="module")
def bt(home_dir):
    # start a beamtime
    pi = "Billinge "
    saf_num = 300000
    wavelength = xpd_wavelength
    experimenters = [["van der Banerjee", "S0ham", 1], ["Terban ", " Max", 2]]
    # copying example longterm config file
    os.makedirs(glbl_dict["xpdconfig"], exist_ok=True)
    pytest_dir = rs_fn("xpdacq", "tests/")
    config = "XPD_beamline_config.yml"
    configsrc = os.path.join(pytest_dir, config)
    shutil.copyfile(configsrc, glbl_dict["blconfig_path"])
    assert os.path.isfile(glbl_dict["blconfig_path"])
    bt = _start_beamtime(
        pi, saf_num, experimenters, wavelength=wavelength, test=True
    )
    # spreadsheet
    xlf = "300000_sample.xlsx"
    src = os.path.join(pytest_dir, xlf)
    shutil.copyfile(src, os.path.join(glbl_dict["import_dir"], xlf))
    import_sample_info(saf_num, bt)
    yield bt
    # when we are done with the glbl delete the folders.
    shutil.rmtree(glbl_dict["home"])


@pytest.fixture(scope="module")
def glbl(bt):
    from xpdacq.glbl import glbl

    if not os.path.exists(glbl["home"]):
        os.makedirs(glbl["home"])
    return glbl


@pytest.fixture(scope="function")
def fresh_xrun(bt, db, set_xpd_configuration):
    xrun = CustomizedRunEngine(None)
    xrun.md["beamline_id"] = glbl_dict["beamline_id"]
    xrun.md["group"] = glbl_dict["group"]
    xrun.md["facility"] = glbl_dict["facility"]
    xrun.ignore_callback_exceptions = False
    xrun.beamtime = bt
    # link mds
    xrun.subscribe(db.v1.insert, "all")
    return xrun


@pytest.fixture(scope="session")
def set_xpd_configuration():
    configure_device(
        db=db,
        shutter=shctl1,
        area_det=simple_pe1c,
        temp_controller=cs700,
        ring_current=ring_current,
        filter_bank=fb,
    )


@pytest.fixture(scope="function")
def exp_hash_uid(bt, fresh_xrun, glbl):
    fresh_xrun.beamtime = bt
    exp_hash_uid = glbl["exp_hash_uid"]
    return exp_hash_uid


@pytest.fixture(scope="module")
def home_dir():
    stem = glbl_dict["home"]
    config_dir = glbl_dict["xpdconfig"]
    archive_dir = glbl_dict["archive_dir"]
    os.makedirs(stem, exist_ok=True)
    yield glbl_dict
    for el in [stem, config_dir, archive_dir]:
        if os.path.isdir(el):
            print("flush {}".format(el))
            shutil.rmtree(el)


@pytest.fixture(scope="session")
def beamline_config_file():
    return rs_fn("xpdacq", "tests/XPD_beamline_config.yml")


@pytest.fixture(scope="function")
def calib_data():
    return devices.CalibrationData(name="calib")


@pytest.fixture(scope="function")
def fake_devices():
    return sim.hw()
