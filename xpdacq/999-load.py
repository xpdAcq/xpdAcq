import os
from xpdacq.glbl import glbl
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime)

# experiment device being used in current plan
try:
    device_list = [pe1c, shctl1, cs700]
    attribute_name = ['area_det', 'shutter', 'temp_controller']

    for attr, device in zip(attribute_name, device_list):
        try:
            setattr(glbl, attr, device)
        except NameError:
            # NameError -> simulation
            pass
except NameError:
    # NameError -> simulation
    pass


# databroker
try:
    setattr(glbl, 'db', db)
except NameError:
    # NameError -> simulation
    pass


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

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir

print('INFO: Initializing the XPD data acquisition environment')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

from xpdacq.calib import *

# analysis functions, only at beamline
#from xpdan.data_reduction import *

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
