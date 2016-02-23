import unittest
import os
import shutil
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment
import xpdacq.beamtimeSetup as bts

class NewExptTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = os.getcwd()
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.PI_name = 'Billinge'
        self.saf_num = 123.67
        self.wavelength = 0.1812
        self.experimenters = [('Banerjee','Soham',1),('Terban ',' Max',2)]
        os.mkdir(self.home_dir)
        self.bt = _execute_start_beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,home_dir=self.home_dir)


    def tearDown(self):
        os.chdir(self.base_dir)
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(self.config_dir):
            shutil.rmtree(self.config_dir)

    def test_new_exp(self):
    	self.yaml_dir = os.path.join(self.home_dir,'config_base','yml')
    	self.assertIsInstance(self.bt,bts.Beamtime)
    	self.assertTrue(os.path.exists(self.yaml_dir))
    	#self.fail('need a test')
