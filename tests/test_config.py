import unittest
import os
#import shutil
#import xpdacq.beamtimeSetup as bts
#from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_prompt_for_PIname,_check_empty_environment


class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.home_dir_name = 'xpdUser'

    def tearDown(self):
        pass
        #if os.path.isdir(self.home_dir):
            #shutil.rmtree(self.home_dir)

    def test_B_DIR(self):
        # test if B_DIR is cwd, for simulation
        from xpdacq.config import B_DIR
        self.assertFalse(B_DIR==os.path.expanduser('~'))
        self.assertTrue(B_DIR==os.getcwd())

    
    def test_object(self):
        # test if objects created are accessible
        from xpdacq.config import pe1c, cs700, LiveTable, shctl1
        
        # basic commands from xpdacq.py, either simulator or real object should pass
        area_det = pe1c
        area_det.cam.acquire_time.put(1.0)
        self.assertEqual(area_det.cam.acquire_time.get(), 1.0)
        
        shutter = shctl1
        shutter.put(1)
        self.assertEqual(shutter.get(),1)
        shutter.put(0)
        self.assertEqual(shutter.get(),0)

        

