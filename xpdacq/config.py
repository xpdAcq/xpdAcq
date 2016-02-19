#!/usr/bin/env python
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
'''Constants and other global definitions.
'''

import os
import runpy
from bluesky.register_mds import register_mds
from bluesky.run_engine import RunEngine

WORKING_DIR = 'xpdUser'
CONFIG_DIR = 'xpdConfig'
XPD_PROFILE_PATH = 'home/xf28id1/.ipython/profile_collection/startup' # make it exact
STARTUP_PATH = os.path.join(XPD_PROFILE_PATH, '00-startup.py')
AREA_DET_PATH = os.path.join(XPD_PROFILE_PATH, '80-areadetector.py')
TEMP_CONTROL_PATH = os.path.join(XPD_PROFILE_PATH, '11-temperature-controller.py')
SHUTTER_PATH = os.path.join(XPD_PROFILE_PATH, '80-areadetector.py')


xpdRE = RunEngine()
xpdRE.md['owner'] = 'xf28id1'
xpdRE.md['beamline_id'] = 'xpd'
xpdRE.md['group'] = 'XPD'


def run_file(full_path):
    ''' run file without importing'''
    return runpy.run_path(full_path)


# import object depends on environment

if os.path.isdir(XPD_PROFILE_PATH):
    print('at XPD')
    B_DIR = os.path.expanduser('~/')
    register_mds(xpdRE)
    
    # collection objects
    pe1c = run_file(AREA_DET_PATH)['pe1c']
    cs700 = run_file(TEMP_CONTROL_PATH)['cs700']
    schtl1 = run_file(SHUTTER_PATH)['schtl1']
    
    from bluesky.broker_callbacks import LiveTables
    LiveTable = LiveTable # TODO - check it!!

    # analysis objects 
    db = run_file(STARTUP_PATH)['db']
    get_events = run_file(STARTUP_PATH)['get_events']
    get_images = run_file(STARTUP_PATH)['get_images']

else:
    print('=== simulation ====')
    from simulator.areadetector import AreaDetector
    from simulator.shutter import shctl1
    from simulator.analysis_obj import verify_files_saved
    from bluesky.examples import motor
    from bluesky.callbacks import LiveTable
    # can't top import as it might not exist

    # collection objects
    B_DIR = os.getcwd()
    pe1c = AreaDetector(0.1)
    cs700 = motor
    shctl1 = shctl1
    LiveTable = LiveTable

    # analysis objects

    # db
    # get_images
    # get_events


class DataPath(object):
    '''Absolute paths to data folders in XPD experiment.
    '''
    _known_keys = [
        'base',
        'raw_config',
        'tif_dir',
        'dark_dir',
        'config_dir',
        'script_dir',
        'export_dir',
        'import_dir',
        'analysis_dir'
    ]

    def __init__(self, stem):
        self.stem = os.path.abspath(os.path.expanduser(stem))

    @property
    def base(self):
        ''' base dir of entire configuration, normally xpdUser '''
        return os.path.join(self.stem, WORKING_DIR)

    @property
    def raw_config(self):
        ''' config dir of entire configuration'''
        return os.path.join(self.stem, CONFIG_DIR)

    @property
    def import_dir(self):
        "Folder for user/beamline scientist import."
        return os.path.join(self.base, 'Import')

    @property
    def export_dir(self):
        "Folder for user output."
        return os.path.join(self.base, 'Export')

    @property
    def tif_dir(self):
        "Folder for saving tiff files."
        return os.path.join(self.base, 'tiff_base')

    @property
    def dark_dir(self):
        "Folder for saving dark tiff files."
        return os.path.join(self.base, 'dark_base')

    @property
    def config_dir(self):
        "Folder for calibration files."
        return os.path.join(self.base, 'config_base')

    @property
    def script_dir(self):
        "Folder for saving script files for the experiment."
        return os.path.join(self.base, 'userScripts')

    @property
    def analysis_dir(self):
        "Folder for saving script files for the experiment."
        return os.path.join(self.base, 'userAnalysis')

    @property
    def allfolders(self):
        "Return a list of all data folder paths for XPD experiment."
        return [getattr(self, k) for k in self._known_keys]

    def __str__(self):
        return '\n'.join('{k}: {v}'.format(k=k, v=getattr(self, k))
                         for k in self._known_keys)

    def __repr__(self):
        return 'DataPath({!r})'.format(self.stem)



