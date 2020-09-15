import os
from pathlib import Path

from xpdacq.xpdacq_conf import glbl_dict
from xpdacq.ipysetup import ipysetup
# useful functions
print("INFO: Import _start_beamtime, _end_beamtime ...")
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
print("INFO: Import import_userScriptsEtc, import_sample_info ...")
from xpdacq.utils import import_userScriptsEtc, import_sample_info
print("INFO: Import ScanPlan, Sample, ct, Tramp, Tlist, tseries ...")
from xpdacq.beamtime import ScanPlan, Sample, ct, Tramp, Tlist, tseries
print("INFO: Import run_calibration ...")
from xpdacq.calib import run_calibration
print("INFO: Import save_last_tiff, save_tiff, integrate_and_save, integrate_and_save_last ...")
from xpdan.data_reduction import save_last_tiff, save_tiff, integrate_and_save, integrate_and_save_last

if glbl_dict["is_simulation"]:
    print("INFO: Start simulation environment ...")
    print("INFO: Import pe1c, shctl1, cs700, db, ring_current, fb ...")
    from xpdsim import xpd_pe1c, shctl1, cs700, db, ring_current, fb
    pe1c = xpd_pe1c
    del xpd_pe1c
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
