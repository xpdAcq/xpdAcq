import unittest
import os
import shutil
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment
import xpdacq.beamtimeSetup as bts
from xpdacq.glbl import glbl

class NewExptTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        self.bt = _execute_start_beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,home_dir=self.home_dir)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))        

    def test_new_exp(self):
    	self.yaml_dir = os.path.join(self.home_dir,'config_base','yml')
    	self.assertIsInstance(self.bt,bts.Beamtime)
    	self.assertTrue(os.path.exists(self.yaml_dir))
    	#self.fail('need a test')
