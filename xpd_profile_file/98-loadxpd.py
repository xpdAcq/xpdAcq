#!/usr/bin/env python
##############################################################################
#
# xpdsim            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Simon Billinge, Chia Hao Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
from xpdacq.config import DataPath
from xpdacq.beamtimeSetup import *
from xpdacq.beamtimeSetup import _make_clean_env
from xpdacq.beamtime import XPD
#from xpdacq.xpdacq import *
#from xpdacq.xpdacq import get_light_images 

# These are needed in the real XPD
WORKING_DIR = 'xpdUser'
B_DIR = os.path.expanduser('~')
#B_DIR = os.getcwd()
datapath = DataPath(B_DIR)

print('Initializing the XPD data acquisition simulation environment') 
_make_clean_env(datapath)

# These are needed in real XPD
os.chdir(os.path.join(B_DIR,WORKING_DIR))
#if there is a yml file in the normal place, then load the beamtime object
bt = XPD.loadyamls()[0]


# instanciate RE:
# imports in this block can be moved up after making sure it is working

import bluesky
from bluesky.run_engine import RunEngine

xpdRE = RunEnginge()
bluesky.register_mds.register_mds(xpdRE)
xpdRE.md['owner'] = 'xf28id1'
xpdRE.md['beamline_id'] = 'xpd'
xpdRE.md['group'] = 'XPD'

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
