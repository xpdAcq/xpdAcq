import unittest
import os
import shutil
import yaml
from time import strftime
from xpdacq.glbl import glbl

import xpdacq.beamtimeSetup as bts
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment, import_yaml
from xpdacq.beamtime import Beamtime,_get_yaml_list
from xpdacq.utils import export_userScriptEtc

class NewBeamtimeTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 123   # must be 123 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        self.saffile = os.path.join(self.config_dir,'saf123.yml')
        #_make_clean_env()
#        self.bt = _execute_start_beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,home_dir=self.home_dir)

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
        usrconfig_dir = os.path.join(self.home_dir,'config_base')
        export_dir = os.path.join(self.home_dir,'Export')
        import_dir = os.path.join(self.home_dir,'Import')
        userysis_dir = os.path.join(self.home_dir,'userAnalysis')
        userscripts_dir = os.path.join(self.home_dir,'userScripts')
        yml_dir = os.path.join(self.home_dir,usrconfig_dir,'yml')
        dirs = _make_clean_env()
        self.assertEqual(dirs,[home_dir,conf_dir,tiff_dir,yml_dir,
            usrconfig_dir,userscripts_dir,export_dir,import_dir,userysis_dir])

    def test_bt_creation(self):
        _make_clean_env()
        self.bt = Beamtime(self.PI_name,self.saf_num,wavelength=self.wavelength,experimenters=self.experimenters,base_dir=self.base_dir)
        self.assertIsInstance(self.bt,Beamtime)
        self.assertEqual(self.bt.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(self.bt.md['bt_piLast'],'Billinge')
        self.assertEqual(self.bt.md['bt_safN'],123)
        self.assertEqual(self.bt.md['bt_wavelength'],0.1812)
        # test empty experimenter
        self.experimenters = []
        bt = Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,Beamtime)
        # test empty PI
        self.PI_name = None
        bt = Beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters)
        self.assertIsInstance(bt,Beamtime)
        #maybe some more edge cases tested here?

    def test_start_beamtime(self):
        os.chdir(self.base_dir)
        # clean environment checked above, so only check a case that works
        os.mkdir(self.home_dir)
        os.mkdir(self.config_dir)
        loadinfo = {'saf number':self.saf_num,'PI last name':self.PI_name,'experimenter list':self.experimenters}
        with open(self.saffile, 'w') as fo:
            yaml.dump(loadinfo,fo)
        self.assertTrue(os.path.isfile(self.saffile))
        bt = _start_beamtime(self.saf_num,home_dir=self.home_dir)
        self.assertEqual(os.getcwd(),self.home_dir) # we should be in home, are we?
        self.assertIsInstance(bt,bts.Beamtime) # there should be a bt object, is there?
        self.assertEqual(bt.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(bt.md['bt_piLast'],'Billinge')
        self.assertEqual(bt.md['bt_safN'],123)
        self.assertEqual(bt.md['bt_wavelength'],None)
        os.chdir(self.base_dir)
        newobjlist = _get_yaml_list()
        strtScnLst = ['bt_bt.yml','ex_l-user.yml','sa_l-user.yml','sp_ct.1s.yml','sp_ct.5s.yml','sp_ct1s.yml','sp_ct5s.yml','sp_ct10s.yml','sp_ct30s.yml']
        self.assertEqual(newobjlist,strtScnLst)
    
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
    def test_export_bt_objects(self):
        self.fail('need to build this function and the tests')
        # user has finished building her yaml files and wants to export to send to Sanjit
        # user types export_bt_objects()
        # program creates an archive file (standard format, autonamed from info in the session)
        # program places the file in Export directory
        # program gives friendly informational statement to user to email the file to Instr. Scientist.

    def test_import_yaml(self):
        src = glbl.import_dir
        dst = glbl.yaml_dir
        os.makedirs(src, exist_ok = True)
        os.makedirs(dst, exist_ok = True)
        # case1 : no files in import_dir, should return nothing
        self.assertEqual(import_yaml(), None)
        # case2 : all three kinds of files together, test if they are successfully move and unpackedsuccesfully
        yaml_name = 'touched.yml'
        tar_name = 'tar_yaml.tar'
        tar_yaml_name = 'tar.yml'
        exception_name = 'yaml.pdf'
        new_yaml = os.path.join(src, yaml_name)
        open(new_yaml, 'a').close()
        new_tar_yaml = os.path.join(src, tar_yaml_name)
        open(new_tar_yaml, 'a').close()
        exception_f = os.path.join(src, exception_name)
        open(exception_f, 'a').close()
        cwd = os.getcwd()
        os.chdir(src) # inevitable step for compression
        (root, ext) = os.path.splitext(tar_name)
        shutil.make_archive(root,'tar') # now data should be in xpdUser/Import/
        os.chdir(cwd)
        os.remove(new_tar_yaml)
        self.assertEqual(import_yaml(), [tar_name, yaml_name])
        import_yaml()
        # confirm valied files are successfully moved and original copy is flushed
        self.assertTrue(yaml_name in os.listdir(dst))
        self.assertTrue(tar_yaml_name in os.listdir(dst))
        self.assertFalse(os.path.isfile(new_yaml))
        self.assertFalse(os.path.isfile(new_tar_yaml))
        # confirm unrecongnized file is left in import dir
        self.assertTrue(os.path.isfile(exception_f))


    def test_export_userScriptEtc(self):
        os.makedirs(glbl.usrScript_dir, exist_ok = True)
        os.makedirs(glbl.yaml_dir, exist_ok = True)
        new_script = os.path.join(glbl.usrScript_dir, 'script.py')
        open(new_script, 'a').close()
        new_yaml = os.path.join(glbl.yaml_dir, 'touched.yml')
        open(new_yaml, 'a').close()
        tar_f_path = export_userScriptEtc()
        shutil.unpack_archive(tar_f_path,glbl.export_dir)
        
        userScript_dir_tail = os.path.split(glbl.usrScript_dir)[1]
        config_base_tail = os.path.split(glbl.config_base)[1]
        yaml_dir_tail = os.path.split(glbl.yaml_dir)[1]
        # are parent dirs in export_dir?
        self.assertTrue(os.path.isdir(os.path.join(glbl.export_dir, userScript_dir_tail)))
        self.assertTrue(os.path.isdir(os.path.join(glbl.export_dir, config_base_tail)))
        # are files in unpacked dirs?
        self.assertTrue('script.py' in os.listdir(os.path.join(glbl.export_dir, userScript_dir_tail)))
        self.assertTrue('touched.yml' in os.listdir(os.path.join(glbl.export_dir, config_base_tail, yaml_dir_tail)))
