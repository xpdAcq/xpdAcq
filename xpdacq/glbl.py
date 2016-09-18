import os
import socket
import time
from unittest.mock import MagicMock
from time import strftime, sleep

import bluesky.examples as be


# define simulated PE1C
class SimulatedPE1C(be.Reader):
    """Subclass the bluesky plain detector examples ('Reader'); add attributes."""

    def __init__(self, name, read_fields):
        self.images_per_set = MagicMock()
        self.images_per_set.get = MagicMock(return_value=5)
        self.number_of_sets = MagicMock()
        self.number_of_sets.put = MagicMock(return_value=1)
        self.number_of_sets.get = MagicMock(return_value=1)
        self.cam = MagicMock()
        self.cam.acquire_time = MagicMock()
        self.cam.acquire_time.put = MagicMock(return_value=0.1)
        self.cam.acquire_time.get = MagicMock(return_value=0.1)
        self._staged = False

        super().__init__(name, read_fields)

        self.ready = True  # work around a hack in Reader

    def stage(self):
        if self._staged:
            raise RuntimeError("Device is already staged.")
        self._staged = True
        return [self]

    def unstage(self):
        self._staged = False


# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
ARCHIVE_BASE_DIR_NAME = 'pe2_data/.userBeamtimeArchive'
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 3000  # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1  # pe1 frame acq time
OWNER = 'xf28id1'
BEAMLINE_ID = 'xpd'
GROUP = 'XPD'
IMAGE_FIELD = 'pe1_image'
CALIB_CONFIG_NAME = 'pyFAI_calib.yml'

# change this to be handled by an environment variable later
hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    simulation = False
else:
    simulation = True

if simulation:
    BASE_DIR = os.getcwd()
else:
    BASE_DIR = os.path.expanduser('~/')

# top directories
HOME_DIR = os.path.join(BASE_DIR, HOME_DIR_NAME)
BLCONFIG_DIR = os.path.join(BASE_DIR, BLCONFIG_DIR_NAME)
ARCHIVE_BASE_DIR = os.path.join(BASE_DIR, ARCHIVE_BASE_DIR_NAME)

# aquire object directories
CONFIG_BASE = os.path.join(HOME_DIR, 'config_base')
YAML_DIR = os.path.join(HOME_DIR, 'config_base', 'yml')
""" Expect dir
config_base/
            yaml/
                bt_bt.yaml
                samples/
                experiments/
                scanplnas/
"""
BT_DIR = YAML_DIR
SAMPLE_DIR = os.path.join(YAML_DIR, 'samples')
EXPERIMENT_DIR = os.path.join(YAML_DIR, 'experiments')
SCANPLAN_DIR = os.path.join(YAML_DIR, 'scanplans')
# other dirs
IMPORT_DIR = os.path.join(HOME_DIR, 'Import')
ANALYSIS_DIR = os.path.join(HOME_DIR, 'userAnalysis')
USERSCRIPT_DIR = os.path.join(HOME_DIR, 'userScripts')
TIFF_BASE = os.path.join(HOME_DIR, 'tiff_base')
USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)

ALL_FOLDERS = [
    HOME_DIR,
    BLCONFIG_DIR,
    YAML_DIR,
    CONFIG_BASE,
    SAMPLE_DIR,
    EXPERIMENT_DIR,
    SCANPLAN_DIR,
    TIFF_BASE,
    USERSCRIPT_DIR,
    IMPORT_DIR,
    ANALYSIS_DIR
]

# directories that won't be tar in the end of beamtime
_EXCLUDE_DIR = [HOME_DIR, BLCONFIG_DIR, YAML_DIR]
_EXPORT_TAR_DIR = [CONFIG_BASE, USERSCRIPT_DIR]


class Glbl:
    _is_simulation = simulation
    beamline_host_name = BEAMLINE_HOST_NAME
    # directory names
    base = BASE_DIR
    home = HOME_DIR
    _export_tar_dir = _EXPORT_TAR_DIR
    xpdconfig = BLCONFIG_DIR
    import_dir = IMPORT_DIR
    config_base = CONFIG_BASE
    tiff_base = TIFF_BASE
    usrScript_dir = USERSCRIPT_DIR
    usrAnalysis_dir = ANALYSIS_DIR
    yaml_dir = YAML_DIR
    bt_dir = BT_DIR
    sample_dir = SAMPLE_DIR
    experiment_dir = EXPERIMENT_DIR
    scanplan_dir = SCANPLAN_DIR
    allfolders = ALL_FOLDERS
    archive_dir = USER_BACKUP_DIR
    # on/off and attributes for functionality
    auto_dark = True
    dk_window = DARK_WINDOW
    _dark_dict_list = [] # initiate a new one every time
    shutter_control = True
    auto_load_calib = True
    calib_config_name = CALIB_CONFIG_NAME
    # beamline name
    owner = OWNER
    beamline_id = BEAMLINE_ID
    group = GROUP
    # instrument config
    det_image_field = IMAGE_FIELD

    # logic to assign correct objects depends on simulation or real experiment
    if not simulation:
        from bluesky.callbacks import LiveTable as lvt
        # import other names to avoid possible self-referencing later
        from databroker import DataBroker
        from databroker import get_images as getImages
        from databroker import get_events as getEvents
        from bluesky.callbacks.broker import verify_files_saved as verifyFiles
        from ophyd import EpicsSignalRO, EpicsSignal
        from bluesky.suspenders import SuspendFloor
        ring_current = EpicsSignalRO('SR:OPS-BI{DCCT:1}I:Real-I',
                                     name='ring_current')
        # real imports
        db = DataBroker
        LiveTable = lvt
        get_events = getEvents
        get_images = getImages
        verify_files_saved = verifyFiles
        # real collection objects will be loaded during start_up
        area_det = None
        temp_controller = None
        shutter = None

    else:
        simulation = True
        # shutter = motor  # this passes as a fake shutter
        archive_dir = os.path.join(BASE_DIR, 'userSimulationArchive')
        # mock imports
        db = MagicMock()
        get_events = MagicMock()
        get_images = MagicMock()
        verify_files_saved = MagicMock()
        # mock collection objects
        area_det = SimulatedPE1C('pe1c', {'intensity': lambda: 5})
        temp_controller = be.motor
        shutter = MagicMock()
        ring_current = MagicMock()
        print('==== Simulation being created in current directory:{} ===='
              .format(BASE_DIR))
        os.makedirs(home, exist_ok=True)

    def __init__(self, frame_acq_time=FRAME_ACQUIRE_TIME):
        self._frame_acq_time = frame_acq_time

    @property
    def frame_acq_time(self):
        return self._frame_acq_time

    @frame_acq_time.setter
    def frame_acq_time(self, val):
        self.area_det.cam.acquire.put(0)
        time.sleep(1)
        self.area_det.number_of_sets.put(1)
        self.area_det.cam.acquire_time.put(val)
        time.sleep(1)
        self.area_det.cam.acquire.put(1)
        print("INFO: area detector has been configured to new"
              " exposure_time = {}s".format(val))
        self._frame_acq_time = val


glbl = Glbl()
