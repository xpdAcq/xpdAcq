import os
import socket
import yaml
import numpy as np
from unittest.mock import MagicMock
from time import strftime, sleep
from xpdacq.mock_objects import mock_shutter, mock_livetable#, Cam, , mock_areadetector

# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
BASE_DIR = os.path.expanduser('~/')
ARCHIVE_BASE_DIR = os.path.expanduser('~/pe2_data/.userBeamtimeArchive')
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 30 # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1 # pe1 frame acq time
OWNER = 'xf28id1'
BEAMLINE_ID = 'xpd'
GROUP = 'XPD'

# directories
HOME_DIR = os.path.join(BASE_DIR, HOME_DIR_NAME)
BLCONFIG_DIR = os.path.join(BASE_DIR, BLCONFIG_DIR_NAME)
EXPORT_DIR = os.path.join(HOME_DIR, 'Export')
YAML_DIR = os.path.join(HOME_DIR, 'config_base', 'yml')
DARK_YAML_NAME = os.path.join(YAML_DIR, '_dark_scan_list.yaml')
CONFIG_BASE = os.path.join(HOME_DIR, 'config_base')
IMPORT_DIR = os.path.join(HOME_DIR, 'Import')

USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)
ALL_FOLDERS = [
        HOME_DIR,
        BLCONFIG_DIR,
        os.path.join(HOME_DIR, 'tiff_base'),
        os.path.join(HOME_DIR, 'dark_base'),
        YAML_DIR,
        CONFIG_BASE,
        os.path.join(HOME_DIR, 'userScripts'),
        EXPORT_DIR,
        IMPORT_DIR,
        os.path.join(HOME_DIR, 'userAnalysis')
]
# for simulation put a summy saf file in BLCONFIG_DIR
os.makedirs(BLCONFIG_DIR, exist_ok=True)
tmp_safname = os.path.join(BLCONFIG_DIR,'saf123.yml')
if not os.path.isfile(tmp_safname):
    dummy_config = {'saf number':123,'PI last name':'simulation','experimenter list':[('PIlastname','PIfirstname',1123456),('Exp2lastname','Exp2firstname',654321),
                     ('Add more lines','as needed, one for each experimenter',98765)]}
    with open(tmp_safname, 'w') as fo:
        yaml.dump(dummy_config,fo)

class glbl():
    beamline_host_name = BEAMLINE_HOST_NAME
    base = BASE_DIR
    home = HOME_DIR
    xpdconfig = BLCONFIG_DIR
    export_dir = EXPORT_DIR
    import_dir = IMPORT_DIR
    config_base = CONFIG_BASE
    yaml_dir = YAML_DIR
    allfolders = ALL_FOLDERS
    archive_dir = USER_BACKUP_DIR
    dk_yaml = DARK_YAML_NAME
    dk_window = DARK_WINDOW
    frame_acq_time = FRAME_ACQUIRE_TIME
    auto_dark = True
    owner = OWNER
    beamline_id = BEAMLINE_ID
    group = GROUP
    ''' this block of code should be taken care in the following block of code. Delete it after testing
    # objects for collection activities
    Msg = None
    xpdRE = None
    Count = None
    AbsScanPlan = None

    area_det = None
    shutter = None
    LiveTable = None
    temp_controller = None

    # objects for analysis activities
    db = None
    get_events = None
    get_images = None
    verify_files_saved = None
    '''
    # logic to assign correct objects depends on simulation or real experiment
    hostname = socket.gethostname()
    if hostname == BEAMLINE_HOST_NAME:
        simulation = False
        from bluesky.run_engine import RunEngine
        from bluesky.register_mds import register_mds
        # import real object as other names to avoid possible self-referencing later
        from bluesky import Msg as msg
        from bluesky.plans import Count as count
        from bluesky.plans import AbsScanPlan as absScanPlan
        from databroker import DataBroker
        from databroker import get_images as getImages
        from databroker import get_events as getEvents
        from bluesky.callbacks import LiveTable as livetable
        from bluesky.broker_callbacks import verify_files_saved as verifyFiles
        xpdRE = RunEngine()
        xpdRE.md['owner'] = glbl.owner
        xpdRE.md['beamline_id'] = glbl.beamline_id
        xpdRE.md['group'] = glbl.group
        register_mds(xpdRE)
        # real imports
        Msg = msg
        Count = count
        db = DataBroker
        LiveTable = livetable
        get_events = getEvents
        get_images = getImages
        AbsScanPlan = absScanPlan 
        verify_files_saved = verifyFiles
        # real collection objects
        area_det = pe1c
        temp_controller = cs700
        shutter = shctl1
        
    else:
        simulation = True
        BASE_DIR = os.getcwd()
        ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,'userSimulationArchive')
        # mock imports
        Msg = MagicMock()
        Count = MagicMock()
        AbsScanPlan = MagicMock()
        db = MagicMock()
        get_events = MagicMock()
        get_images = MagicMock()
        LiveTable = mock_livetable
        verify_files_saved = MagicMock()
        # mock collection objects
        xpdRE = MagicMock()
        temp_controller = MagicMock()
        shutter = mock_shutter()
        area_det = MagicMock()
        area_det.cam = MagicMock()
        area_det.cam.acquire_time = MagicMock()
        area_det.cam.acquire_time.put = MagicMock(return_value=0.1)
        area_det.cam.acquire_time.get = MagicMock(return_value=0.1)
        area_det.number_of_sets = MagicMock()
        area_det.number_of_sets.put = MagicMock(return_value=1)
        print('==== Simulation being created in current directory:{} ===='.format(BASE_DIR))

# this line never gets executed 
#if __name__ == '__main__':
    #print(glbl.dp().home)

