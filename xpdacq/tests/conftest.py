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
from pathlib import Path
import databroker
import os
import pytest
import shutil
from pkg_resources import resource_filename as rs_fn
from xpdsim import (
    cs700,
    simple_pe1c,
    shctl1,
    ring_current,
    xpd_wavelength,
    fb
)

from xpdacq.beamtimeSetup import _start_beamtime
from xpdacq.utils import import_sample_info
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.xpdacq_conf import glbl_dict, configure_device


@pytest.fixture
def db():
    return databroker.v2.temp()


@pytest.fixture
def bt(flush_dir, beamline_config_file, sample_xlsx, glbl):
    pi = "Billinge "
    saf_num = 300000
    wavelength = xpd_wavelength
    experimenters = [["van der Banerjee", "S0ham", 1], ["Terban ", " Max", 2]]
    shutil.copyfile(beamline_config_file, glbl["blconfig_path"])
    bt = _start_beamtime(
        pi, saf_num, experimenters, wavelength=wavelength, test=True
    )
    shutil.copyfile(sample_xlsx, Path(glbl["import_dir"]) / sample_xlsx.name)
    import_sample_info(saf_num, bt)
    return bt


@pytest.fixture
def glbl():
    from xpdacq.glbl import glbl
    return glbl


@pytest.fixture
def fresh_xrun(bt, db):
    # set simulation objects
    # alias
    pe1c = simple_pe1c
    configure_device(
        db=db,
        shutter=shctl1,
        area_det=pe1c,
        temp_controller=cs700,
        ring_current=ring_current,
        filter_bank=fb,
    )
    from bluesky import RunEngine
    xrun = CustomizedRunEngine(None)
    xrun.md["beamline_id"] = glbl_dict["beamline_id"]
    xrun.md["group"] = glbl_dict["group"]
    xrun.md["facility"] = glbl_dict["facility"]
    xrun.ignore_callback_exceptions = True
    xrun.beamtime = bt
    # link mds
    xrun.subscribe(db.v1.insert, "all")
    return xrun


@pytest.fixture
def exp_hash_uid(bt, fresh_xrun, glbl):
    fresh_xrun.beamtime = bt
    exp_hash_uid = glbl["exp_hash_uid"]
    return exp_hash_uid


@pytest.fixture
def flush_dir(request, glbl):
    """Create the necessary directory and delete after the test is finished."""
    folders = list(
        map(
            Path,
            [
                glbl["base"],
                glbl["home"],
                glbl["xpdconfig"]
            ]
        )
    )
    for folder in folders:
        if folder.is_dir():
            shutil.rmtree(folder)
    for folder in folders:
        folder.mkdir()

    def finish():
        for folder1 in folders + [Path(glbl["archive_dir"])]:
            if folder1.is_dir():
                shutil.rmtree(folder1)

    request.addfinalizer(finish)
    return


@pytest.fixture(scope="session")
def beamline_config_file():
    return Path(rs_fn("xpdacq", "tests/XPD_beamline_config.yml"))


@pytest.fixture(scope="session")
def sample_xlsx():
    return Path(rs_fn("xpdacq", "tests/300000_sample.xlsx"))
