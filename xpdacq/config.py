#!/usr/bin/env python

'''Constants and other global definitions.
'''

import os.path

WORKING_DIR = 'xpdUser'
CONFIG_DIR = 'xpdConfig'

class DataPath(object):
    '''Absolute paths to data folders in XPD experiment.
    '''

    base = os.path.expanduser('~/'+WORKING_DIR)
    raw_config = os.path.expanduser('~/'+CONFIG_DIR)

    @property
    def tif(self):
        "Folder for saving tiff files."
        return os.path.join(self.base, 'tif_base')

    @property
    def dark(self):
        "Folder for saving dark tiff files."
        return os.path.join(self.base, 'dark_base')

    @property
    def config(self):
        "Folder for calibration files."
        return os.path.join(self.base, 'config_base')

    @property
    def script(self):
        "Folder for saving script files for the experiment."
        return os.path.join(self.base, 'script_base')

    @property
    def allfolders(self):
        "Return a list of all data folder paths for XPD experiment."
        rv = [self.base, self.raw_config, self.tif, self.dark, self.config, self.script]
        return rv

# class DataPath


# unique instance of the DataPath class.
datapath = DataPath()
