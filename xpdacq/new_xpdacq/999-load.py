import os
from xpdacq.new_xpdacq.glbl import glbl
from xpdacq.new_xpdacq.beamtimeSetup import start_xpdacq
from xpdacq.new_xpdacq.beamtime import *

try:
    # if pe1c and other exits, i.e. at XPD 
    glbl.area_det = pe1c
    glbl.shutter = shctl1
    glbl.temp_controller = cs700
except NameError:
    pass

from xpdacq.new_xpdacq.xpdacq import *
# beamtime reload happen in xpdacq

# gonna seperate analysis from collection
#from xpdacq.analysis import * 

HOME_DIR = glbl.home
BASE_DIR = glbl.base
YAML_DIR = glbl.yaml_dir

print('INFO: Initializing the XPD data acquisition environment')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
