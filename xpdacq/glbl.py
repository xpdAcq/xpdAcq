import os
import socket
import yaml
from time import strftime

# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
BASE_DIR = os.path.expanduser('~/pe2_data')
ARCHIVE_BASE_DIR = os.path.expanduser('~/pe2_data/.userBeamtimeArchive')
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 15 # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1 # pe1 frame acq time

def _areaDET(area_det_name):
    global AREA_DET
    AREA_DET = area_det_name

def _tempController(temp_controller_name):
    global TEMP_CONTROLLER
    TEMP_CONTROLLER = temp_controller_name

def _shutter(shutter_name):
    global SHUTTER
    SHUTTER = shutter_name

hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    # real experiment
    pass
    #bluesky.register_mds.register_mds(xpdRE)
else:
    BASE_DIR = os.getcwd()
    ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,'userSimulationArchive')
    print('==== Simulation being created in current directory:{} ===='.format(BASE_DIR))
HOME_DIR = os.path.join(BASE_DIR, HOME_DIR_NAME)
BLCONFIG_DIR = os.path.join(BASE_DIR, BLCONFIG_DIR_NAME)
EXPORT_DIR = os.path.join(HOME_DIR, 'Export')
YAML_DIR = os.path.join(HOME_DIR, 'config_base', 'yml')
DARK_YAML_NAME = os.path.join(YAML_DIR, '_dark_scan_list.yaml')

USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)
ALL_FOLDERS = [
        HOME_DIR,
        BLCONFIG_DIR,
        os.path.join(HOME_DIR, 'tiff_base'),
        os.path.join(HOME_DIR, 'dark_base'),
        YAML_DIR,
        os.path.join(HOME_DIR, 'config_base'),
        os.path.join(HOME_DIR, 'userScripts'),
        EXPORT_DIR,
        os.path.join(HOME_DIR, 'Import'),
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
    #this behavior can be changed to include Tim's logic
    base = BASE_DIR
    home = HOME_DIR
    xpdconfig = BLCONFIG_DIR
    export_dir = EXPORT_DIR
    yaml_dir = YAML_DIR
    allfolders = ALL_FOLDERS
    archive_dir = USER_BACKUP_DIR
    beamhost = BEAMLINE_HOST_NAME
    dk_yaml = DARK_YAML_NAME
    dk_window = DARK_WINDOW
    frame_acq_time = FRAME_ACQUIRE_TIME

if __name__ == '__main__':
    print(glbl.dp().home)
