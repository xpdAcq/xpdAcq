import os
import copy
import time
import uuid
import shutil
import unittest

from xpdacq.glbl import glbl
from xpdacq.beamtimeSetup import (_load_glbl, _configure_devices)

class glblTest(unittest.TestCase):
    def setUp(self):
        self.glbl = glbl
        for el in self.glbl.allfolders:
            os.makedirs(el, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.glbl.home)
        if os.path.isdir(self.glbl.archive_dir):
            shutil.rmtree(self.glbl.archive_dir)

    def test_glbl_reload(self):
        reload_glbl = copy.copy(self.glbl)  # glbl going to be reload
        # fresh start, test default values
        assert self.glbl.dk_window == 3000
        assert self.glbl.auto_dark == True
        assert self.glbl._dark_dict_list == []
        assert self.glbl.mask == None
        # update value
        self.glbl.dk_window = 20
        self.glbl.auto_dark = False
        self.glbl._dark_dict_list = [{'acq_time': 0.1, 'exposure': 0.5,
                                      'timestamp': time.time(),
                                      'uid':str(uuid.uuid4())}]
        # after update, local yaml should exist
        assert os.path.isfile(self.glbl.filepath)
        _load_glbl(reload_glbl)
        # test equality of two glbl classes
        for k, v in self.glbl.__dict__.items():
            assert reload_glbl.__dict__[k] == v
    
    def test_configure_devices(self):
        _configure_devices(self.glbl)
        # confirm synthetic objects are attached to glbl class
        self.glbl.area_det.name = 'pe1c'
        self.temp_controller = 'cs700'
        self.shutter = 'shctl1'
