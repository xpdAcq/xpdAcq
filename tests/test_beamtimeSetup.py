import unittest
import os
import shutil
from time import strftime
from xpdacq.xpdacq import _areaDET
from xpdacq.xpdacq import _tempController
from xpdacq.xpdacq import _shutter
from xpdacq.xpdacq import _bdir
from xpdacq.xpdacq import _cdir
from xpdacq.xpdacq import _hdir
from xpdacq.xpdacq import _hostname
from xpdacq.glbl import glbl

import xpdacq.beamtimeSetup as bts
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment


class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
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

    def test_check_empty_environment(self):
        #sanity check. xpdUser directory exists.  First make sure the code works right when it doesn't exist.
        self.assertFalse(os.path.isdir(self.home_dir))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        #now put something there but make it a file instead of a directory
        self.newfile = os.path.join(self.base_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        #now make it the proper thing...xpdUser directory'
        os.mkdir(self.home_dir)
        self.assertTrue(os.path.isdir(self.home_dir))
        #but put a wrongly named file in it
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        #os.remove(self.newfile)
        #if it is just a tar file it will pass (tested below) but if there is a tar file plus sthg else it should fail with RuntimeError
        self.newfile2 = os.path.join(self.home_dir,'touched.tar')
        open(self.newfile2, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile2))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        os.remove(self.newfile2)
        #now do the same but with directories
        self.newdir = os.path.join(self.home_dir,'userJunk')
        os.mkdir(self.newdir)
        self.assertTrue(os.path.isdir(self.newdir))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        #add a badly named file
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)
        #add a tar file, but should still fail because there is also another directory there
        self.newfile = os.path.join(self.home_dir,'touched.tar')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(SystemExit, lambda:_check_empty_environment(base_dir = self.base_dir))
        os.remove(self.newfile)

    def test_make_clean_env(self):
        home_dir = os.path.join(self.base_dir,'xpdUser')
        conf_dir = os.path.join(self.base_dir,'xpdConfig')
        tiff_dir = os.path.join(self.home_dir,'tiff_base')
        dark_dir = os.path.join(self.home_dir,'dark_base')
        usrconfig_dir = os.path.join(self.home_dir,'config_base')
        export_dir = os.path.join(self.home_dir,'Export')
        import_dir = os.path.join(self.home_dir,'Import')
        userysis_dir = os.path.join(self.home_dir,'userAnalysis')
        userscripts_dir = os.path.join(self.home_dir,'userScripts')
        yml_dir = os.path.join(self.home_dir,usrconfig_dir,'yml')
        #dp = DataPath(self.base_dir)
        dirs = _make_clean_env()
        self.assertEqual(dirs,[home_dir,conf_dir,tiff_dir,dark_dir,yml_dir,
            usrconfig_dir,userscripts_dir,export_dir,import_dir,userysis_dir])

    def test_mybt_creation(self):
        self.bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,base_dir=self.base_dir)
        self.assertIsInstance(self.bt,bts.Beamtime)
        self.assertEqual(self.bt.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        #self.assertEqual(self.bt.md['bt_experimenters'],[('me','you')])
        self.assertEqual(self.bt.md['bt_piLast'],'Billinge')
        self.assertEqual(self.bt.md['bt_safN'],123)
        self.assertEqual(self.bt.md['bt_wavelength'],0.1812)
        # test empty experimenter
        self.experimenters = []
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)
        # test empty PI
        self.PI_name = None
        bt = bts.Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,bts.Beamtime)
        #maybe some more edge cases tested here?
    
    def test_start_beamtime(self):
        os.chdir(self.base_dir)
        # clean encironment checked above, so only check a case that works
        os.mkdir(self.home_dir)
        bt = _execute_start_beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,home_dir=self.home_dir)
        self.assertEqual(os.getcwd(),self.home_dir) # we should be in home, are we?
        self.assertIsInstance(bt,bts.Beamtime) # there should be a bt object, is there?
        self.assertEqual(bt.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(bt.md['bt_piLast'],'Billinge')
        self.assertEqual(bt.md['bt_safN'],123)
        self.assertEqual(bt.md['bt_wavelength'],0.1812)
        os.chdir(self.base_dir)
    
    @unittest.expectedFailure
    def test_execute_end_beamtime(self):
        os.mkdir(self.home_dir)
        #self.assertRaises(OSError, lambda: _end_beamtime(base_dir=self.base_dir,bto=self.bt))
        self.fail('finish making the test')
        #archive_dir = os.path.expanduser(strftime('./pe2_data/2016/userBeamtimeArchive'))

    @unittest.expectedFailure
    def test_delete_home_dir_tree(self):
        self.fail('need to build tests for this function')

    @unittest.expectedFailure
    def test_inputs_in_end_beamtime(self):
        self.fail('need to refactor this function and build the tests')

    @unittest.expectedFailure
    def test_load_user_yml(self):
        self.fail('need to build this function and the tests')
        # after start_beamtime, Sanjit places user yml.tar (or some other archive format) file into xpdUser directory
        # then runs _load_user_yml() which unpacks and installs it in yml_dir

    @unittest.expectedFailure
    def test_export_bt_objects(self):
        self.fail('need to build this function and the tests')
        # user has finished building her yaml files and wants to export to send to Sanjit
        # user types export_bt_objects()
        # program creates an archive file (standard format, autonamed from info in the session)
        # program places the file in Export directory
        # program gives friendly informational statement to user to email the file to Instr. Scientist.

    