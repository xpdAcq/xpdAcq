import os
import socket
import time
import yaml
from time import strftime, sleep

from xpdacq.yamlclass import YamlClass

# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
ARCHIVE_BASE_DIR_NAME = 'pe1_data/.userBeamtimeArchive'
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 3000  # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1  # pe1 frame acq time
OWNER = 'xf28id1'
BEAMLINE_ID = 'xpd'
GROUP = 'XPD'
IMAGE_FIELD = 'pe1_image'
CALIB_CONFIG_NAME = 'pyFAI_calib.yml'
MASK_NAME = 'xpdacq_mask.npy'

# change this to be handled by an environment variable later
hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    simulation = False
else:
    simulation = True

if simulation:
    BASE_DIR = os.getcwd()
else:
    BASE_DIR = os.path.abspath('/direct/XF28ID1/pe2_data')

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


class Glbl(YamlClass):
    """A class stores global options of xpdAcq"""
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
    if simulation:
        archive_dir = os.path.join(BASE_DIR,
                                   'userSimulationArchive')
    else:
        archive_dir = USER_BACKUP_DIR
    # on/off and attributes for functionality
    auto_dark = True
    dk_window = DARK_WINDOW
    _dark_dict_list = [] # initiate a new one every time
    shutter_control = True
    auto_load_calib = True
    calib_config_name = CALIB_CONFIG_NAME
    _frame_acq_time = FRAME_ACQUIRE_TIME
    # beamline name
    owner = OWNER
    beamline_id = BEAMLINE_ID
    group = GROUP
    # instrument config
    det_image_field = IMAGE_FIELD
    mask_name = MASK_NAME
    calib_config_dict = None
    mask = None

    # object should be handled by ipython profile
    db = None
    area_det = None
    temp_controller = None
    shutter = None
    verify_files_saved = None

    # default masking dict
    mask_dict = {'edge': 30, 'lower_thresh': 0.0,
                 'upper_thresh': None, 'bs_width': 13,
                 'tri_offset': 13, 'v_asym': 0,
                 'alpha': 2.5, 'tmsk': None}

    def __init__(self, filepath, internal_dict={}):
        super().__init__(internal_dict)
        self._filepath = filepath

    def allowed_attributes(self):
        """define a list of attribute names that are allowed to be
        yamlize"""
        return ['auto_dark', 'dk_window', '_dark_dict_list',
                'shutter_control', 'auto_load_calib',
                'calib_config_name','calib_config_dict',
                '_frame_acq_time', 'mask', 'mask_dict']

    @property
    def frame_acq_time(self):
        return self._frame_acq_time

    @frame_acq_time.setter
    def frame_acq_time(self, val):
        """special method to configure frame acqusition time"""
        self.area_det.cam.acquire.put(0)
        time.sleep(1)
        self.area_det.number_of_sets.put(1)
        self.area_det.cam.acquire_time.put(val)
        time.sleep(1)
        self.area_det.cam.acquire.put(1)
        print("INFO: area detector has been configured to new"
              " acquisition_time = {}s".format(val))
        self._frame_acq_time = val

glbl_filepath = os.path.join(CONFIG_BASE, 'glbl.yml')
glbl = Glbl(glbl_filepath)
