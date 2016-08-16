import os
from xpdacq.glbl import glbl
from xpdacq.beamtime import *
from xpdacq.utils import import_sample
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime)

if not glbl._is_simulation:
    glbl.area_det = pe1c
    glbl.shutter = shctl1
    glbl.temp_controller = cs700
    # let NameError handle missing object


# beamtime reload happen in xpdacq
from xpdacq.xpdacq import *

# instantiate prun without beamtime, like bluesky setup
prun = CustomizedRunEngine(None)
prun.md['owner'] = glbl.owner
prun.md['beamline_id'] = glbl.beamline_id
prun.md['group'] = glbl.group

# load beamtime
bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
    prun.beamtime = bt

# gonna seperate analysis from collection
from xpdacq.analysis import *

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir

print('INFO: Initializing the XPD data acquisition environment')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

from xpdacq.calib import run_calibration
print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
