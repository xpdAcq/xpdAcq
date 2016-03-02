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
from xpdacq.glbl import _areaDET
from xpdacq.glbl import _tempController
from xpdacq.glbl import _shutter
# holding as this could be done by direct import
#from xpdacq.glbl import _verify_write
#from xpdacq.glbl import _LiveTable
''' not ready yet
from xpdacq.glbl import _db
from xpdacq.glbl import _getEvents
from xpdacq.glbl import _getImages
'''
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import XPD

_areaDET(pe1c)
_tempController(cs700)
_shutter(shctl1)

# FIXME - collection objects related to filestore. change to this import if xpdSim is completely ready
#_verify_write(verify_files_saved)

# FIXME - analysis objects will be used in analysis environment. change to this import if xpdSim is completely ready
#_LiveTable(LiveTable)
#_dataBroker(db)
#_getEvents(get_events)
#_getImages(get_images)

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir
BEAMLINE_HOST_NAME = glbl.beamhost

# FIXME - extra directories are created when importing certain function, which leads logic loop hole in start_beamtime
# XPD creates config_base/yml and export_data() creates Exports/

print('Initializing the XPD data acquisition simulation environment') 
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

#if there is a yml file in the normal place, then this was an existing experiment that was interrupted.
#if len(XPD.loadyamls()) > 0:  --> this will create extra directory 
if os.path.isdir(YAML_DIR):
    print("loading bt_bt.yml")
    tmp = XPD()
    bt = tmp.loadyamls()[0]

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
