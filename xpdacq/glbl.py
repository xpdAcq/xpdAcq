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
    '''
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
        # real experiment
        simulation = False
        from bluesky.run_engine import RunEngine
        from bluesky.register_mds import register_mds
        from bluesky import Msg
        from bluesky.plans import Count
        from bluesky.plans import AbsScanPlan
        xpdRE = RunEngine()
        xpdRE.md['owner'] = glbl.owner
        xpdRE.md['beamline_id'] = glbl.beamline_id
        xpdRE.md['group'] = glbl.group
        register_mds(xpdRE)
    else:
        simulation = True
        BASE_DIR = os.getcwd()
        ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,'userSimulationArchive')
        xpdRE = MagicMock()
        # magic mock objects
        Msg = MagicMock()
        Count = MagicMock()
        AbsScanPlan = MagicMock()
        cs700 = MagicMock()
        db = MagicMock()
        get_events = MagicMock()
        get_images = MagicMock()
        verify_files_saved = MagicMock()
        ########################
        shutter = mock_shutter()
        LiveTable = mock_livetable
        area_det = MagicMock()
        area_det.cam = MagicMock()
        area_det.cam.acquire_time = MagicMock()
        area_det.cam.acquire_time.put = MagicMock(return_value=0.1)
        area_det.cam.acquire_time.get = MagicMock(return_value=0.1)
        area_det.number_of_sets = MagicMock()
        area_det.number_of_sets.put = MagicMock(return_value=1)
        print('==== Simulation being created in current directory:{} ===='.format(BASE_DIR))

#if __name__ == '__main__':
    #print(glbl.home)
    #glbl.Msg = Msg

