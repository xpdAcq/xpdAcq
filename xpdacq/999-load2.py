import os
from pathlib import Path

from bluesky.callbacks.zmq import Publisher
from databroker.v2 import temp
from xpdsim import xpd_pe1c, shctl1, cs700, ring_current, fb

from xpdacq.beamtime import ScanPlan, Sample, ct, Tramp, Tlist, tseries
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.calib import run_calibration
from xpdacq.ipysetup import ipysetup
from xpdacq.utils import import_userScriptsEtc, import_sample_info
from xpdacq.xpdacq_conf import xpd_configuration

pe1c = xpd_pe1c

db = temp()

_start_beamtime = _start_beamtime
_end_beamtime = _end_beamtime
import_userScriptsEtc = import_userScriptsEtc
import_sample_info = import_sample_info
ScanPlan = ScanPlan
Sample = Sample
ct = ct
Tramp = Tramp
Tlist = Tlist
tseries = tseries
run_calibration = run_calibration
xpd_configuration = xpd_configuration
print("INFO: Initializing the XPD data acquisition environment ...")
glbl, bt, xrun = ipysetup(
    area_det=pe1c,
    shutter=shctl1,
    temp_controller=cs700,
    filter_bank=fb,
    ring_current=ring_current,
    db=db
)
print("INFO: Initialized glbl, bt, xrun.")
xrun.subscribe(Publisher("localhost:5567", prefix=b'raw'))
print("INFO: Publish data to localhost port 5567 with prefix 'raw'.")
if Path(glbl["home"]).is_dir():
    os.chdir(glbl["home"])
    print("INFO: Changed home to {}".format(glbl["home"]))
elif Path(glbl["base"]).is_dir():
    os.chdir(glbl["base"])
    print("INFO: Changed home to {}".format(glbl["base"]))
print(
    "OK, ready to go.  To continue, follow the steps in the xpdAcq"
    "documentation at http://xpdacq.github.io/xpdacq"
)
# delete useless names
del os, Path, ipysetup, Publisher, temp, xpd_pe1c
