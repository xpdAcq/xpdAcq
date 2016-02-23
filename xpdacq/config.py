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

import os.path
import xpdacq.object_manage as main

B_DIR = main.B_DIR
HOME_DIR = 'xpdUser'
CONFIG_DIR = 'xpdConfig'

# base = B_DIR = dp.base = '~'
# home = HOME_DIR = dp.home = 'xpdUser'


class DataPath(object):
    '''Absolute paths to data folders in XPD experiment.
    '''
    _known_keys = [
        'home',
        'raw_config',
        'tiff_dir',
        'dark_dir',
        'yaml_dir',
        'config_dir',
        'script_dir',
        'export_dir',
        'import_dir',
        'analysis_dir'
    ]

    def __init__(self, stem):
        self.stem = os.path.abspath(os.path.expanduser(stem))

    @property
    def home(self):
        ''' base dir of entire configuration, normally xpdUser '''
        return os.path.join(self.stem, HOME_DIR)

    @property
    def raw_config(self):
        ''' config dir of entire configuration'''
        return os.path.join(self.stem, CONFIG_DIR)

    @property
    def import_dir(self):
        "Folder for user/beamline scientist import."
        return os.path.join(self.home, 'Import')

    @property
    def export_dir(self):
        "Folder for user output."
        return os.path.join(self.home, 'Export')

    @property
    def tiff_dir(self):
        "Folder for saving tiff files."
        return os.path.join(self.home, 'tiff_base')

    @property
    def dark_dir(self):
        "Folder for saving dark tiff files."
        return os.path.join(self.home, 'dark_base')
    
    @property
    def config_dir(self):
        "Folder for calibration files."
        return os.path.join(self.home, 'config_base')

    @property
    def yaml_dir(self):
        "Folder for saving yaml files"
        return os.path.join(self.home, 'config_base', 'yml')


    @property
    def script_dir(self):
        "Folder for saving script files for the experiment."
        return os.path.join(self.home, 'userScripts')

    @property
    def analysis_dir(self):
        "Folder for saving script files for the experiment."
        return os.path.join(self.home, 'userAnalysis')

    @property
    def allfolders(self):
        "Return a list of all data folder paths for XPD experiment."
        return [getattr(self, k) for k in self._known_keys]

    def __str__(self):
        return '\n'.join('{k}: {v}'.format(k=k, v=getattr(self, k))
                         for k in self._known_keys)

    def __repr__(self):
        return 'DataPath({!r})'.format(self.stem)

