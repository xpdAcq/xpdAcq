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
from xpdacq.xpdacq_conf import (glbl_dict, configure_device,
                                _reload_glbl, _set_glbl)

# configure experiment device being used in current version
if glbl_dict['is_simulation']:
    from xpdacq.simulation import pe1c, db, cs700, shctl1

    configure_device(area_det=pe1c, shutter=shctl1,
                     temp_controller=cs700, db=db)
else:
    # FIXME: create synthetic ring current object in fullness of time
    from ophyd import EpicsSignalRO

    ring_current = EpicsSignalRO('SR:OPS-BI{DCCT:1}I:Real-I',
                                 name='ring_current')
    configure_device(area_det=pe1c, shutter=shctl1,
                     temp_controller=cs700, db=db,
                     ring_current=ring_current)

# cache previous glbl state
reload_glbl_dict = _reload_glbl()
from xpdacq.glbl import glbl

# reload beamtime
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime)

bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
if reload_glbl_dict is not None:
    _set_glbl(glbl, reload_glbl_dict)

# import necessary modules
from xpdacq.xpdacq import *
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info

# instantiate xrun without beamtime, like bluesky setup
xrun = CustomizedRunEngine(None)
xrun.md['beamline_id'] = glbl['beamline_id']
xrun.md['group'] = glbl['group']
xrun.md['facility'] = glbl['facility']

# insert header to db, either simulated or real
xrun.subscribe(db.insert, 'all')

if bt:
    xrun.beamtime = bt

HOME_DIR = glbl['home']
BASE_DIR = glbl['base']

print('INFO: Initializing the XPD data acquisition environment\n')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

from xpdacq.calib import *

# analysis functions, only at beamline
from xpdan.data_reduction import *

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq\n')
