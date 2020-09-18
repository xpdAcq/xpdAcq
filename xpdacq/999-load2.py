import os
from pathlib import Path
from xpdan.data_reduction import save_last_tiff, save_tiff, integrate_and_save, integrate_and_save_last

from xpdacq.beamtime import ScanPlan, Sample, ct, Tramp, Tlist, tseries
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.calib import run_calibration
from xpdacq.ipysetup import ipysetup
from xpdacq.utils import import_userScriptsEtc, import_sample_info
from xpdacq.xpdacq_conf import glbl_dict
from xpdacq.xpdacq_conf import xpd_configuration

if glbl_dict["is_simulation"]:
    from xpdsim import xpd_pe1c, shctl1, cs700, db, ring_current, fb

    pe1c = xpd_pe1c
    del xpd_pe1c

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
save_last_tiff = save_last_tiff
save_tiff = save_tiff
integrate_and_save = integrate_and_save
integrate_and_save_last = integrate_and_save_last
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
home = glbl["home"] if Path(glbl["home"]).is_dir() else glbl["base"]
os.chdir(home)
print("INFO: Changed home to {}".format(home))
print(
    "OK, ready to go.  To continue, follow the steps in the xpdAcq"
    "documentation at http://xpdacq.github.io/xpdacq"
)
# delete useless names
del os, Path, glbl_dict, ipysetup, home
