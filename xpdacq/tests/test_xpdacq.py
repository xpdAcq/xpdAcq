import copy
import pytest
import databroker
import numpy as np
import ophyd
import os
import shutil
import time
import unittest
import uuid
import warnings
import yaml
from bluesky.callbacks import collector
from pathlib import Path
from pkg_resources import resource_filename as rs_fn
from xpdsim import dexela

from xpdacq.beamtime import ScanPlan, ct, Tramp, tseries, Tlist
from xpdacq.beamtime import _nstep
from xpdacq.beamtimeSetup import _start_beamtime
from xpdacq.glbl import glbl
from xpdacq.simulation import pe1c, cs700, shctl1, fb
from xpdacq.tools import xpdAcqException
from xpdacq.utils import import_sample_info
from xpdacq.xpdacq import (
    _validate_dark,
    CustomizedRunEngine,
    _auto_load_calibration_file,
    set_beamdump_suspender,
)
from xpdacq.xpdacq_conf import (
    configure_device,
    XPDACQ_MD_VERSION,
    _load_beamline_config,
)
from xpdacq.xpdacq_conf import xpd_configuration
from bluesky.plans import count


@pytest.mark.parametrize(
    "sample, plan",
    [
        (0, 0)
    ]
)
def test_xrun(fresh_xrun, sample, plan):
    xrun = fresh_xrun
    xrun(sample, plan)

