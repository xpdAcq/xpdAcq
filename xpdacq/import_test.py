import numpy as np

from bluesky import Msg
from bluesky.plans import Count
from bluesky.plans import AbsScanPlan

from xpdacq.control import _open_shutter
from xpdacq.control import _close_shutter
from xpdacq.beamtime import Union, Xposure

# import collection object
from xpdacq.config import pe1c
from xpdacq.config import xpdRE
from xpdacq.config import cs700
print('Before you start, make sure the area detector IOC is in "Acquire mode"')

FRAME_ACQUIRE_TIME = 0.1
# assigning for xpdacq namespace
area_det = pe1c
area_det.cam.acquire_time.put(FRAME_ACQUIRE_TIME)
temp_controller = cs700


