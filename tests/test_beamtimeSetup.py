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
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)

    def test_dont_start_beamtime_dir_not_empty(self):
        # finds an extra directory so won't start
        os.mkdir(os.path.join(self.home_dir,'OldUserJunk')) 
        self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        # finds an extra non-tar file so won't start
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))

    def test_start_beamtime(self):
        #cleanup!
        shutil.rmtree(self.home_dir)
        #_start_beamtime(base_dir = self.base_dir)