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
"""Configuration of python object and gloabal constents
"""

import os
from xpdacq.glbl import glbl
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import *

try:
    # if pe1c and other exits, i.e. at XPD 
    glbl.area_det = pe1c
    glbl.shutter = shctl1
    glbl.temp_controller = cs700
except NameError:
    pass

from xpdacq.xpdacq import *
from xpdacq.analysis import *

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir

print('Initializing the XPD data acquisition simulation environment')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

# if there is a yml file in the normal place, then this was an existing experiment that was interrupted.
# if os.path.isdir(YAML_DIR):
bt_fname = os.path.join(YAML_DIR, "bt_bt.yml")
if os.path.isfile(bt_fname):
    print("loading bt_bt.yml")
    tmp = XPD()
    bt = tmp.loadyamls()[0]

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
