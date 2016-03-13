#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
'''Configuration of python object and gloabal constents
'''

import os
import socket
from xpdacq.glbl import glbl
#from xpdacq.glbl import _areaDET
#from xpdacq.glbl import _tempController
# test at xpd
#from xpdacq.glbl import _shutter
#from xpdacq.glbl import _verify_write
#from xpdacq.glbl import _LiveTable
#from xpdacq.glbl import _dataBroker
#from xpdacq.glbl import _getEvents
#from xpdacq.glbl import _getImages
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import *

#_areaDET(pe1c)
#_tempController(cs700)

#######
# watch out, some testing here
#######
#_shutter(shctl1)

# try to keep attribute names the same as the way we are goona use. Can be
# changed later


# logic to make correct objects depends on simulation or real experiment
hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    # real experiment
    simulation = False
    from bluesky.run_engine import RunEngine
    from bluesky.register_mds import register_mds
    from bluesky import Msg
    from bluesky.plans import Count
    from bluesky.plans import AbsScanPlan

    xpdRE = RunEngine()
    xpdRE.md['owner'] = glbl.owner
    xpdRE.md['beamline_id'] = glbl.beamline_id
    xpdRE.md['group'] = glbl.group
    register_mds(xpdRE)
else:
    simulation = True
    BASE_DIR = os.getcwd()
    ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,'userSimulationArchive')
    xpdRE = MagicMock()
    shutter = mock_shutter()
    LiveTable = mock_livetable
    #area_det = mock_areadetector()
    area_det = MagicMock()
    area_det.cam = MagicMock()
    area_det.cam.acquire_time = MagicMock()
    area_det.cam.acquire_time.put = MagicMock(return_value=1)
    area_det.cam.acquire_time.get = MagicMock(return_value=1)
    area_det.number_of_sets = MagicMock()
    area_det.number_of_sets.put = MagicMock(return_value=1)
    print('==== Simulation being created in current directory:{} ===='.format(BASE_DIR))

# objects for collection activities
glbl.Msg = Msg
glbl.xpdRE = xpdRE
glbl.Count = Count
glbl.AbsScanPlan = AbsScanPlan
glbl.area_det = pe1c
glbl.shutter = shctl1
glbl.LiveTable = LiveTable
glbl.temp_controller = cs700

# objects for analysis activities
glbl.db = db
glbl.get_events = get_events
glbl.get_images = get_images
glbl.verify_files_saved = verify_files_saved


# revisit these and remove them
#_shutter(shctl1)
#_verify_write(verify_files_saved)
#_LiveTable(LiveTable)
#_dataBroker(db)
#_getEvents(get_events)
#_getImages(get_images)

from xpdacq.xpdacq import *
from xpdacq.analysis import *

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir
BEAMLINE_HOST_NAME = glbl.beamhost

print('Initializing the XPD data acquisition simulation environment') 
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

#if there is a yml file in the normal place, then this was an existing experiment that was interrupted.
#if os.path.isdir(YAML_DIR):
bt_fname = os.path.join(YAML_DIR, "bt_bt.yml")
if os.path.isfile(bt_fname):
    print("loading bt_bt.yml")
    tmp = XPD()
    bt = tmp.loadyamls()[0]

# XPD test
if not os.path.isfile(glbl.dk_yaml):
    print('init dark_yaml')
    XPD()._init_dark_scan_list()
print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
