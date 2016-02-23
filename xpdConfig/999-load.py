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
'''Configuration of python object and gloabal constents
'''

import os
import socket
from xpdacq.object_manage import _areaDET
from xpdacq.object_manage import _tempController
from xpdacq.object_manage import _shutter
from xpdacq.object_manage import _bdir

''' not ready yet
from xpdacq.object_manage import _db
from xpdacq.object_manage import _getEvents
from xpdacq.object_manage import _getImages
'''

import bluesky
from bluesky.run_engine import RunEngine

# instanciate RE:
# imports in this block can be moved up after making sure it is working
xpdRE = RunEngine()
xpdRE.md['owner'] = 'xf28id1'
xpdRE.md['beamline_id'] = 'xpd'
xpdRE.md['group'] = 'XPD'

HOME_DIR = 'xpdUser'
CONFIG_DIR = 'xpdConfig'
XPD_HOST_NAME = 'xf28id1-ws2'

# Note:
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

# differentiate simulation or reall experiment based on hostname
# this method might be refactored soon

hostname = socket.gethostname()
if hostname == 'xf28id1-ws2':
    # real experiment
    B_DIR = os.path.expanduser('~/pe2_data')
    _bdir(B_DIR)
    dp = DataPath(B_DIR) 
    # TODO - haven't fully cleaned dp yet, but will refactor later
    bluesky.register_mds.register_mds(xpdRE)


else:
    print('==== Simulation ====')
    B_DIR = os.getcwd()
    _bdir(B_DIR)
    dp = DataPath(B_DIR)

# can't top import as objects are just created above
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.beamtime import XPD
# FIXME - extra directories are created when importing certain function, which leads logic loop hole in start_beamtime
# XPD creates config_base/yml and export_data() creates Exports/

print('Initializing the XPD data acquisition simulation environment') 
os.chdir(os.path.join(B_DIR, HOME_DIR))

#if there is a yml file in the normal place, then load the beamtime object
#if len(XPD.loadyamls()) > 0: try alternative logic, load in yaml only if yaml_dir exists
if os.path.isdir(dp.yaml_dir):
    bt = XPD.loadyamls()[0]

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq')
