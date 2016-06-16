from xpdacq.new_xpdacq import (CustomizedRunEngine, load_beamtime, 
                               start_xpdacq)
bt = start_xpdacq()
if bt is not None:
    prun = CustomizedRunEngine(bt)


# define simulated PE1C
class SimulatedPE1C(Reader):
    "Subclass the bluesky plain detector examples ('Reader'); add attributes."
    def __init__(self, name, fields):
        self.images_per_set = MagicMock()
        self.images_per_set.get = MagicMock(return_value=5)
        self.number_of_sets = MagicMock()
        self.number_of_sets.put = MagicMock(return_value=1)
        self.number_of_sets.get = MagicMock(return_value=1)
        self.cam = MagicMock()
        self.cam.acquire_time = MagicMock()
        self.cam.acquire_time.put = MagicMock(return_value=0.1)
        self.cam.acquire_time.get = MagicMock(return_value=0.1)

        super().__init__(name, fields)

        self.ready = True  # work around a hack in Reader


def setup_module():
    glbl.pe1c = SimulatedPE1C('pe1c', ['pe1c'])
    glbl.shutter = motor  # this passes as a fake shutter
    glbl.frame_acq_time = 0.1
    glbl._dark_dict_list = []


# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
ARCHIVE_BASE_DIR_NAME = 'pe2_data/.userBeamtimeArchive'
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 3000 # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1 # pe1 frame acq time
OWNER = 'xf28id1'
BEAMLINE_ID = 'xpd'
GROUP = 'XPD'


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
# directories
HOME_DIR = os.path.join(BASE_DIR, HOME_DIR_NAME)
BLCONFIG_DIR = os.path.join(BASE_DIR, BLCONFIG_DIR_NAME)
ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,ARCHIVE_BASE_DIR_NAME)
YAML_DIR = os.path.join(HOME_DIR, 'config_base', 'yml')
DARK_YAML_NAME = os.path.join(YAML_DIR, '_dark_scan_list.yaml')
CONFIG_BASE = os.path.join(HOME_DIR, 'config_base')
IMPORT_DIR = os.path.join(HOME_DIR, 'Import')
USERSCRIPT_DIR = os.path.join(HOME_DIR, 'userScripts')
TIFF_BASE = os.path.join(HOME_DIR, 'tiff_base')
ALLOWED_SCANPLAN_TYPE =['ct', 'Tramp', 'tseries']

USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)
ALL_FOLDERS = [
        HOME_DIR,
        BLCONFIG_DIR,
        YAML_DIR,
        CONFIG_BASE,
        TIFF_BASE,
        USERSCRIPT_DIR,
        IMPORT_DIR,
        os.path.join(HOME_DIR, 'userAnalysis')
]

