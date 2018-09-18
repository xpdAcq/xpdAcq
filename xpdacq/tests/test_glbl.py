import os
import copy
import time
import uuid
import shutil
import unittest

from xpdacq.xpdacq_conf import (GlblYamlDict, glbl_dict,
                                _reload_glbl, _set_glbl,
                                configure_device)

from xpdacq.simulation import pe1c, cs700, shctl1, db, fb


class glblTest(unittest.TestCase):
    def setUp(self):
        self._glbl = GlblYamlDict('glbl',
                                  **glbl_dict)  # glbl going to be tested
        for el in self._glbl['allfolders']:
            os.makedirs(el, exist_ok=True)
        # set simulation objects
        configure_device(area_det=pe1c, temp_controller=cs700,
                         shutter=shctl1, db=db, filter_bank=fb)

    def tearDown(self):
        shutil.rmtree(self._glbl['home'])
        if os.path.isdir(self._glbl['archive_dir']):
            shutil.rmtree(self._glbl['archive_dir'])

    def test_glbl_reload(self):
        # fresh start, test default values
        for k, v in glbl_dict.items():
            assert self._glbl[k] == v
        # update value
        self._glbl['dk_window'] = 20
        self._glbl['auto_dark'] = False
        self._glbl['_dark_dict_list'] = [{'acq_time': 0.1, 'exposure': 0.5,
                                          'timestamp': time.time(),
                                          'uid': str(uuid.uuid4())}]
        # after update, local yaml should exist
        assert os.path.isfile(self._glbl['glbl_yaml_path'])
        reload_glbl_dict = _reload_glbl()
        # test contents of reload dict
        for k, v in self._glbl.items():
            assert reload_glbl_dict[k] == v
        # test equality of glbl objects after setting contents
        reload_glbl = GlblYamlDict('glbl', **glbl_dict)
        _set_glbl(reload_glbl, reload_glbl_dict)
        assert reload_glbl == self._glbl

    def test_glbl_swap(self):
        self._glbl['dk_window'] = 20
        assert self._glbl['dk_window'] == 20
        with self._glbl.swap(dk_window=1000):
            assert self._glbl['dk_window'] == 1000
            glbl2 = self._glbl.from_yaml(open(self._glbl.filepath, 'r'))
            assert glbl2 is not self._glbl
            assert glbl2['dk_window'] == 20
        assert self._glbl['dk_window'] == 20
