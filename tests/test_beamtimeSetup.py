import unittest
import os
import shutil
from time import strftime
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment

class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = os.getcwd()
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.PI_name = 'Billinge'
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('Banerjee','Soham',1),('Terban','Max',2)]
        self.bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)


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
        self.assertIsInstance(self.bt,bts.Beamtime)
        self.assertEqual(self.bt.md['bt_experimenters'],[('Banerjee','Soham',1),('Terban','Max',2)])
        self.assertEqual(self.bt.md['bt_piLast'],'Billinge')
        self.assertEqual(self.bt.md['bt_safN'],123)
        self.assertEqual(self.bt.md['bt_wavelength'],0.1812)
        # test empty experimenters
        self.experimenters = []
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)
        # test empty PI
        self.PI_name = None
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)

    def test_start_beamtime(self):
        os.chdir(self.base_dir)
        os.mkdir(self.home_dir)
        piname = 'Billinge'
        safn = 1234
        wavelength = 0.1818
        explist = [('Banerjee','Soham',1),('Terban','Max',2)]
        tryagain = _execute_start_beamtime(piname,safn,wavelength,explist,base_dir=self.base_dir)

    def test_end_beamtime(self):
        os.mkdir(self.home_dir)
        #self.assertRaises(OSError, lambda: _end_beamtime(base_dir=self.base_dir,bto=self.bt))
        #self.fail('finish making the test')
        archive_dir = os.path.expanduser(strftime('./pe2_data/2016/userBeamtimeArchive'))