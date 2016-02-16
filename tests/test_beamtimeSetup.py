import unittest
import os
import shutil
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_prompt_for_PIname,_check_empty_environment

class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = os.getcwd()
        self.home_dir = os.path.join(self.base_dir,'xpdUser')

    def tearDown(self):
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)

    def test_check_empty_environment(self):
        #sanity check. xpdUser directory exists.  First make sure it doesn't exist.
        self.assertFalse(os.path.exists(self.home_dir))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        #now put something there but make it a file instead of a directory
        self.newfile = os.path.join(self.base_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        #now make it the proper thing...xpdUser directory'
        os.mkdir(self.home_dir)
        self.assertTrue(os.path.isdir(self.home_dir))
        #but put a wrongly named file in it
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        #os.remove(self.newfile)
        #if it is just a tar file it will pass (tested below) but if there is a tar file plus sthg else it should fail with RuntimeError
        self.newfile2 = os.path.join(self.home_dir,'touched.tar')
        open(self.newfile2, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile2))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        os.remove(self.newfile2)
        #now do the same but with directories
        self.newdir = os.path.join(self.home_dir,'userJunk')
        os.mkdir(self.newdir)
        self.assertTrue(os.path.isdir(self.newdir))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        #add a badly named file
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        #add a tar file, but should still fail because there is also another directory there
        self.newfile = os.path.join(self.home_dir,'touched.tar')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(RuntimeError, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)


    def test_bt_creation(self):
        self.PI_name = 'Billinge'
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('Banerjee','Soham',1),('Terban','Max',2)]
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)
        self.assertEqual(bt.md['bt_experimenters'],[('Banerjee','Soham',1),('Terban','Max',2)])
        self.assertEqual(bt.md['bt_piLast'],'Billinge')
        self.assertEqual(bt.md['bt_safN'],123)
        self.assertEqual(bt.md['bt_wavelength'],0.1812)
        # test empty experimenters
        self.experimenters = []
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)
        # test empty PI
        self.PI_name = None
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)