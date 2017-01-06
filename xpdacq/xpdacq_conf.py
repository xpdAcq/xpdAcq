#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import socket
import time
import yaml
from time import strftime, sleep
from xpdacq.yamldict import YamlDict

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
GLBL_YAML_NAME = 'glbl.yml'

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
SCANPLAN_DIR = os.path.join(YAML_DIR, 'scanplans')
# other dirs
IMPORT_DIR = os.path.join(HOME_DIR, 'Import')
ANALYSIS_DIR = os.path.join(HOME_DIR, 'userAnalysis')
USERSCRIPT_DIR = os.path.join(HOME_DIR, 'userScripts')
TIFF_BASE = os.path.join(HOME_DIR, 'tiff_base')
USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)
GLBL_YAML_PATH = os.path.join(YAML_DIR, GLBL_YAML_NAME)
MASK_PATH = os.path.join(CONFIG_BASE, MASK_NAME)

ALL_FOLDERS = [
    HOME_DIR,
    BLCONFIG_DIR,
    YAML_DIR,
    CONFIG_BASE,
    SAMPLE_DIR,
    SCANPLAN_DIR,
    TIFF_BASE,
    USERSCRIPT_DIR,
    IMPORT_DIR,
    ANALYSIS_DIR
]

# directories that won't be tar in the end of beamtime
_EXCLUDE_DIR = [HOME_DIR, BLCONFIG_DIR, YAML_DIR]
_EXPORT_TAR_DIR = [CONFIG_BASE, USERSCRIPT_DIR]


glbl_dict = dict(is_simulation=simulation,
                 # beamline info
                 owner=OWNER,
                 beamline_id=BEAMLINE_ID,
                 group=GROUP,
                 beamline_host_name=BEAMLINE_HOST_NAME,
                 # directory names
                 base=BASE_DIR,
                 home=HOME_DIR,
                 _export_tar_dir=_EXPORT_TAR_DIR,
                 xpdconfig=BLCONFIG_DIR,
                 import_dir=IMPORT_DIR,
                 config_base=CONFIG_BASE,
                 tiff_base=TIFF_BASE,
                 usrScript_dir=USERSCRIPT_DIR,
                 usrAnalysis_dir=ANALYSIS_DIR,
                 yaml_dir=YAML_DIR,
                 bt_dir=BT_DIR,
                 sample_dir=SAMPLE_DIR,
                 scanplan_dir=SCANPLAN_DIR,
                 allfolders=ALL_FOLDERS,
                 archive_dir=USER_BACKUP_DIR,
                 glbl_yaml_path=GLBL_YAML_PATH,
                 mask_path=MASK_PATH,
                 # options for functionalities
                 frame_acq_time=FRAME_ACQUIRE_TIME,
                 auto_dark=True,
                 dk_window=DARK_WINDOW,
                 _dark_dict_list=[],
                 shutter_control=True,
                 auto_load_calib=True,
                 calib_config_name=CALIB_CONFIG_NAME,
                 mask_dict={'edge': 30, 'lower_thresh': 0.0,
                            'upper_thresh': None, 'bs_width': 13,
                            'tri_offset': 13, 'v_asym': 0,
                            'alpha': 2.5, 'tmsk': None},
                 # instrument config
                 det_image_field=IMAGE_FIELD
                 )


# special function and dict to store all necessary objects
xpd_device = {}
def setup_xpdacq(*, area_det, shutter, temp_controller, db, **kwargs):
    """ function to set up required device/objects for xpdacq """
    # specifically assign minimum requirements
    xpd_device['area_det'] = area_det
    xpd_device['shutter'] = shutter
    xpd_device['temp_controller'] = temp_controller
    xpd_device['db'] = db
    # extra kwargs
    xpd_device.update(**kwargs)


def configure_frame_acq_time(new_frame_acq_time):
    """ function to configure frame acquire time of area detector """

    area_det = xpd_device['area_det']
    # stop acquisition
    area_det.cam.acquire.put(0)
    time.sleep(1)
    area_det.number_of_sets.put(1)
    area_det.cam.acquire_time.put(new_frame_acq_time)
    # extra wait time for device to set
    time.sleep(1)
    area_det.cam.acquire.put(1)
    print("INFO: area detector has been configured to new "
          "exposure_time = {}s".format(new_frame_acq_time))


class xpdAcqException(Exception):
    # customized class for xpdAcq-related exception
    pass


class GlblYamlDict(YamlDict):
    """ class holds global options of xpdAcq.

    It automatically update yaml file when contents are changed,
    and for back-support, it issues a Deprecationwarning when user tries
    to set attributes

    Parameters:
    -----------
    name : str
        name of this object. It's *suggested* to be the same as
        the instance name. i.e. glbl = GlblYamlDict('glbl', **kwargs)
    kwargs :
        keyword arguments for global options
    """
    # required attributes for yaml
    _VALID_ATTRS = ['_name', '_filepath', 'filepath', '_referenced_by']

    # keys for fields allowed to change
    _MUTABLE_FIELDS = ['frame_acq_time', 'auto_dark', 'dk_window',
                       '_dark_dict_list', 'shutter_control',
                       'auto_load_calib', 'calib_config_name',
                       'mask_dict', 'det_image_field']

    def __init__(self, name, **kwargs):
        super().__init__(name=name,**kwargs)
        self._referenced_by = []
        self._name = name

    def default_yaml_path(self):
        return GLBL_YAML_PATH

    def __setitem__(self, key, val):
        if key not in self._MUTABLE_FIELDS:
            raise xpdAcqException("key='{}' is not allowed to change!"
                                  .format(key))
        else:
            # annoying logic specifically for area_det
            if key == 'frame_acq_time':
                configure_frame_acq_time(val)
            super().__setitem__(key, val)

    def __setattr__(self, key, val):
        if key not in self._VALID_ATTRS:
            if key in (self._MUTABLE_FIELDS):
                # back-support
                raise DeprecationWarning("{} has been changed, please do "
                                         "this command instead\n"
                                         ">>> {}['{}']={}"
                                         .format(self._name,
                                                 self._name,
                                                 key, val))
            else:
                raise AttributeError("{} doesn't support setting attribute"
                                     .format(self._name))
        else:
            super().__setattr__(key, val)

    @classmethod
    def from_yaml(cls, f):
        d = yaml.load(f)
        instance = cls.from_dict(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

