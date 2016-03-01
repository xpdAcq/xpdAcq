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

_areaDET(pe1c)
''' not ready yet
from xpdacq.xpdacq import _db
from xpdacq.xpdacq import _getEvents
from xpdacq.xpdacq import _getImages
'''

import bluesky
from bluesky.run_engine import RunEngine

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir
BEAMLINE_HOST_NAME = glbl.beamhost

# instanciate RE:
# imports in this block can be moved up after making sure it is working
xpdRE = RunEngine()
xpdRE.md['owner'] = 'xf28id1'
xpdRE.md['beamline_id'] = 'xpd'
xpdRE.md['group'] = 'XPD'

hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    bluesky.register_mds.register_mds(xpdRE)

from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import XPD
# FIXME - extra directories are created when importing certain function, which leads logic loop hole in start_beamtime
# XPD creates config_base/yml and export_data() creates Exports/

print('Initializing the XPD data acquisition simulation environment') 
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

#if there is a yml file in the normal place, then this was an existing experiment that was interrupted.
#if len(XPD.loadyamls()) > 0:  --> this will create extra directory 
#if os.path.isdir(YAML_DIR):
    #print("loading bt_bt.yml")
    #tmp = XPD()
    #bt = tmp.loadyamls()[0]

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
