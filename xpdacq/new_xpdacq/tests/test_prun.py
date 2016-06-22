import unittest
import os
import shutil
import yaml
import uuid
from time import strftime

# FIXME
from xpdacq.new_xpdacq.glbl import glbl
from xpdacq.new_xpdacq.beamtime import *
from xpdacq.new_xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime)
from xpdacq.new_xpdacq.xpdacq import _validate_dark

class NewBeamtimeTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = '123'   # must be 123 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))


    def test_validate_dark(self):
        """ test login in this function """
        # no dark_dict_list
        self.assertFalse(glbl._dark_dict_list)
        rv = _validate_dark()
        self.assertEqual(rv, None)
        # initiate dark_dict_list
        # light cnt time is always 0.5 in mock detector, for now..
        dark_dict_list=[]
        now = time.time()

        # case1: adjust exposure time
        for i in range(5):
            dark_dict_list.append({'uid':str(uuid.uuid4()),
                                   'exposure':(i+1)*0.1,
                                   'timestamp':now})
        glbl._dark_dict_list = dark_dict_list
        correct_uid = [el['uid'] for el in dark_dict_list if
                       el['exposure'] == 0.5]
        self.assertEqual(len(correct_uid), 1)
        rv = _validate_dark()
        self.assertEqual(rv, correct_uid[-1])

        # case2: adjust expire time
        dark_dict_list = []
        for i in range(5):
            dark_dict_list.append({'uid':str(uuid.uuid4()),
                                   'exposure': 0.5,
                                   'timestamp':now-(i+1)*60})
        glbl._dark_dict_list = dark_dict_list
        correct_uid = [el['uid'] for el in dark_dict_list
                       if el['timestamp']- time.time() <=
                       (glbl.dk_window*60 -0.1)]
        # large window
        rv = _validate_dark()
        self.assertEqual(rv, correct_uid[-1]) 
        # small window
        rv = _validate_dark(0.1)
        self.assertEqual(rv, None)
        # medium window
        rv = _validate_dark(1.5)
        correct_uid = dark_dict_list[0]['uid']
        self.assertEqual(rv, correct_uid) 
