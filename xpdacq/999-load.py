#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
from xpdacq.glbl import glbl, setup_xpdacq
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime)

# configure experiment device being used in current version
if glbl['is_simulation']:
    from xpdacq.simulation import pe1c, db, cs700, shctl1
setup_xpdacq(area_det=pe1c, shutter=shctl1,
             temp_controller=cs700, db=db)

# beamtime reload happen in xpdacq
from xpdacq.xpdacq import *

# instantiate xrun without beamtime, like bluesky setup
xrun = CustomizedRunEngine(None)
xrun.md['owner'] = glbl['owner']
xrun.md['beamline_id'] = glbl['beamline_id']
xrun.md['group'] = glbl['group']

# insert header to db, either simulated or real
xrun.subscribe('all', db.mds.insert)

# load beamtime
bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
    xrun.beamtime = bt

HOME_DIR = glbl['home']
BASE_DIR = glbl['base']

print('INFO: Initializing the XPD data acquisition environment\n')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

#from xpdacq.calib import *

# analysis functions, only at beamline
#from xpdan.data_reduction import *

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq\n')
