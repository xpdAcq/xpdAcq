import os
import copy
import time
import uuid
import shutil
import unittest

from xpdacq.glbl import Glbl, glbl_filepath
from xpdacq.beamtimeSetup import (_load_glbl, _configure_devices)

class glblTest(unittest.TestCase):
    def setUp(self):
        self._glbl  = Glbl(glbl_filepath) # glbl going to be tested
        for el in self._glbl.allfolders:
            os.makedirs(el, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self._glbl.home)
        if os.path.isdir(self._glbl.archive_dir):
            shutil.rmtree(self._glbl.archive_dir)

    def test_glbl_reload(self):
        reload_glbl = copy.copy(self._glbl)  # glbl going to be reload
        # fresh start, test default values
        assert self._glbl.dk_window == 3000
        assert self._glbl.auto_dark == True
        assert self._glbl._dark_dict_list == []
        assert self._glbl.mask == None
        # update value
        self._glbl.dk_window = 20
        self._glbl.auto_dark = False
        self._glbl._dark_dict_list = [{'acq_time': 0.1, 'exposure': 0.5,
                                  'timestamp': time.time(),
                                  'uid':str(uuid.uuid4())}]
        # after update, local yaml should exist
        assert os.path.isfile(self._glbl.filepath)
        assert self._glbl.filepath == glbl_filepath
        _load_glbl(reload_glbl)
        # test equality of two glbl classes
        for k, v in self._glbl.__dict__.items():
            assert reload_glbl.__dict__[k] == v

    def test_configure_devices(self):
        _configure_devices(self._glbl)
        # confirm synthetic objects are attached to glbl class
        assert self._glbl.area_det.name == 'pe1c'
        assert self._glbl.temp_controller.name == 'cs700'
        assert self._glbl.shutter.name == 'shctl1'
