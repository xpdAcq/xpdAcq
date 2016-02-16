import unittest
import os
import shutil
import xpdacq.beamtimeSetup
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime
#import IPython.testing as ipt 

class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = os.getcwd()
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        os.mkdir(self.home_dir)
    def tearDown(self):
        shutil.rmtree(self.home_dir)

    def test_dont_start_beamtime_dir_not_empty(self):
        # finds an extra directory so won't start
        os.mkdir(os.path.join(self.home_dir,'OldUserJunk')) 
        self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        # finds an extra non-tar file so won't start
        os.chdir(self.home_dir)
        open('touched.txt', 'a').close()
        self.assertTrue(os.path.isfile(os.path.join(self.home_dir,'touched.txt')))
        os.chdir(self.base_dir)
        #self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        #
        #self.home_dir = os.getcwd()
        
        #self.assertTrue(os.path.isdir(home_dir))
        #
        #
        #try:
        #    _start_beamtime()
        #except RuntimeError:
        #    self.assertTrue(True)


        # Sanjit runs a _start_beamtime

        # end_beamtime has not successfully run and the env is not empty
