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
from xpdacq.glbl import glbl
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime, _load_glbl,
                                  _configure_devices)

# configure experiment device being used in current version
if glbl._is_simulation:
    _configure_devices(glbl)
else:
    # at beamline
    _configure_devices(glbl, area_det=pe1c, shutter=shctl1,
                       temp_controller=cs700, db=db)

# beamtime reload happen in xpdacq
from xpdacq.xpdacq import *

# instantiate xrun without beamtime, like bluesky setup
xrun = CustomizedRunEngine(None)
xrun.md['owner'] = glbl.owner
xrun.md['beamline_id'] = glbl.beamline_id
xrun.md['group'] = glbl.group

# load beamtime
bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
    xrun.beamtime = bt
    # reload glbl options
    _load_glbl(glbl)

HOME_DIR = glbl.home
BASE_DIR = glbl.base

print('INFO: Initializing the XPD data acquisition environment\n')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

from xpdacq.calib import *

# analysis functions, only at beamline
#from xpdan.data_reduction import *

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq\n')
