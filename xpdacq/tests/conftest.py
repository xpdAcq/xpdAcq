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
import sys
import shutil
import asyncio
import numpy as np
import time
import pytest
from xpdacq.xpdacq_conf import (glbl_dict,
                                configure_device,
                                xpd_configuration)

from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.beamtimeSetup import _start_beamtime
from xpdacq.utils import import_sample_info, ExceltoYaml
from xpdsim import (cs700, xpd_pe1c, simple_pe1c, shctl1, ring_current,
                    xpd_wavelength, fb)


from pkg_resources import resource_filename as rs_fn


@pytest.fixture(scope='module')
def db():
    from xpdsim import db, sim_db_dir
    yield db
    # NOTE: do not flush for now since test might be caught in the
    # middle of flushing/creating database
    #if os.path.exists(sim_db_dir):
    #    print('Flush db dir')
    #    shutil.rmtree(sim_db_dir)

@pytest.fixture(scope='module')
def bt(home_dir):
    # start a beamtime
    PI_name = 'Billinge '
    saf_num = 300000
    wavelength = xpd_wavelength
    experimenters = [('van der Banerjee', 'S0ham', 1),
                     ('Terban ', ' Max', 2)]
    # copying example longterm config file
    os.makedirs(glbl_dict['xpdconfig'], exist_ok=True)
    pytest_dir = rs_fn('xpdacq', 'tests/')
    config = 'XPD_beamline_config.yml'
    configsrc = os.path.join(pytest_dir, config)
    shutil.copyfile(configsrc, os.path.join(glbl_dict['xpdconfig'], config))
    assert(os.path.isfile(os.path.join(glbl_dict['xpdconfig'], config)))            
    bt = _start_beamtime(PI_name, saf_num,
                         experimenters,
                         wavelength=wavelength,test=True)
    # spreadsheet
    xlf = '300000_sample.xlsx'
    src = os.path.join(pytest_dir, xlf)
    shutil.copyfile(src, os.path.join(glbl_dict['import_dir'], xlf))
    import_sample_info(saf_num, bt)
    yield bt


@pytest.fixture(scope='function')
def glbl(bt):
    from xpdacq.glbl import glbl
    if not os.path.exists(glbl['home']):
        os.makedirs(glbl['home'])
    yield glbl
    # when we are done with the glbl delete the folders.
    shutil.rmtree(glbl['home'])


@pytest.fixture(scope='module')
def fresh_xrun(bt, db):
    # loop
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    # create xrun
    xrun = CustomizedRunEngine(None, loop=loop)
    xrun.md['beamline_id'] = glbl_dict['beamline_id']
    xrun.md['group'] = glbl_dict['group']
    xrun.md['facility'] = glbl_dict['facility']
    xrun.ignore_callback_exceptions = False
    # link mds
    xrun.subscribe(db.insert, 'all')
    # set simulation objects
    # alias
    pe1c = simple_pe1c
    configure_device(db=db, shutter=shctl1,
                     area_det=pe1c, temp_controller=cs700,
                     ring_current=ring_current, filter_bank=fb)
    yield xrun
    # clean
    print("Clean xrun loop")
    if xrun.state != 'idle':
        xrun.halt()
    ev = asyncio.Event(loop=loop)
    ev.set()
    loop.run_until_complete(ev.wait())


@pytest.fixture(scope='function')
def exp_hash_uid(bt, fresh_xrun, glbl):
    fresh_xrun.beamtime = bt
    exp_hash_uid = glbl['exp_hash_uid']
    yield exp_hash_uid


@pytest.fixture(scope='module')
def home_dir():
    stem = glbl_dict['home']
    config_dir = glbl_dict['xpdconfig']
    archive_dir = glbl_dict['archive_dir']
    os.makedirs(stem, exist_ok=True)
    yield glbl_dict
    for el in [stem, config_dir, archive_dir]:
        if os.path.isdir(el):
            print("flush {}".format(el))
            shutil.rmtree(el)
