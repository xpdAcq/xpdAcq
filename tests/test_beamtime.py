import unittest
import os
import shutil
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtime import XPD,Beamtime
from xpdacq.glbl import glbl
from xpdacq.beamtime import _clean_name,_clean_md_input,_update_objlist,_get_yaml_list
from xpdacq.beamtime import *

class NewExptTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        #_make_clean_env()
        self.bt = _execute_start_beamtime(self.PI_name,self.saf_num,self.wavelength,self.experimenters,home_dir=self.home_dir)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))        

    def test_clean_name(self):
    	# make sure yaml dir and bt object exists
    	name = ' my test experiment '
    	cleaned = _clean_name(name)
    	self.assertEqual(cleaned,'mytestexperiment')
    	name = ' my way too long experiment name from hell. Dont let users do this already! '
    	self.assertRaises(SystemExit, lambda:_clean_name(name))
    	# what if user gives something that is not a string?
    	name = []
    	self.assertRaises(SystemExit, lambda:_clean_name(name))
    
    @unittest.expectedFailure
    def test_yaml_path(self):
    	self.fail('need a test for _yaml_path')

    @unittest.expectedFailure
    def test_loadyamls(self):
        self.fail('need a test for loadyamls')

    def test_yamify(self):
        xpdobj = XPD()
        xpdobj.name = ' test'
        xpdobj.type = 'b t'
        yaml_dir = glbl.yaml_dir
        objlist = []
        lname = os.path.join(yaml_dir,'_acqobj_list.yml')
        #initialize the objlist yaml file if it doesn't exist
        if not os.path.isfile(lname):
            fo = open(lname, 'w')
            yaml.dump(objlist, fo)
        testfname = os.path.join(yaml_dir,'bt_test.yml')
        probe = xpdobj._yamify()
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','bt_test.yml'])
        xpdobj2 = XPD()
        xpdobj2.name = ' test2'
        xpdobj2.type = 'b t'
        testfname2 = os.path.join(yaml_dir,'bt_test2.yml')
        probe2 = xpdobj2._yamify()
        newobjlist2 = _get_yaml_list()
        self.assertEqual(newobjlist2,['bt_bt.yml','bt_test.yml','bt_test2.yml'])
        self.assertEqual(probe,testfname)
        self.assertTrue(os.path.isfile(probe))
        # try adding another item that is already there
        probe3 = xpdobj2._yamify()
        newobjlist3 = _get_yaml_list()
        self.assertEqual(newobjlist3,['bt_bt.yml','bt_test.yml','bt_test2.yml'])

#        olist = xpdobj.loadyamls()
#        self.assertEqual(olist[0].name,'bt')
#        self.assertEqual(olist[0].type,'bt')

    def test_update_objlist(self):
        objlist = []
        newobjlist = _update_objlist(objlist,'testme')
        self.assertEqual(newobjlist,['testme'])
        newobjlist2 = _update_objlist(newobjlist,'testme2')
        self.assertEqual(newobjlist2,['testme','testme2'])
        newobjlist3 = _update_objlist(newobjlist2,'testme2')
        self.assertEqual(newobjlist3,['testme','testme2'])

    def test_get_obj_uid(self):
        name = 'bt'
        otype = 'bt'
        bt = Beamtime('me',123,321,[])
        uid1 = bt._get_obj_uid('bt','bt')
        self.assertNotEqual(uid1,'')
        bt = Beamtime('you',123,321,[])
        uid2 = bt._get_obj_uid('bt','bt')
        self.assertEqual(uid1,uid2)

    def test_make_experiment(self):
        name = 'myexp '
        self.ex = Experiment(name,self.bt)
        self.assertIsInstance(self.ex,Experiment)
        self.assertEqual(self.ex.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(self.ex.md['bt_piLast'],'Billinge')
        self.assertEqual(self.ex.md['bt_safN'],123)
        self.assertEqual(self.ex.md['bt_wavelength'],0.1812)
        self.assertEqual(self.ex.md['ex_name'],'myexp')
        uid1 = self.ex.md['ex_uid']
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml'])
        self.ex2 = Experiment(' your exp',self.bt)
        self.assertEqual(self.ex2.md['ex_name'],'your exp')
        uid2 = self.ex2.md['ex_uid']
        self.assertNotEqual(uid1,uid2)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml','ex_yourexp.yml'])
        self.ex3 = Experiment(' your exp',self.bt)
        self.assertEqual(self.ex3.md['ex_name'],'your exp')
        uid3 = self.ex3.md['ex_uid']
        self.assertEqual(uid2,uid3)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml','ex_yourexp.yml'])

    def test_make_sample(self):
        name = 'my sample '
        self.ex = Experiment('myexp',self.bt)
        self.sa = Sample(name,self.ex)
        self.assertIsInstance(self.sa,Sample)
        self.assertEqual(self.sa.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(self.sa.md['bt_piLast'],'Billinge')
        self.assertEqual(self.sa.md['bt_safN'],123)
        self.assertEqual(self.sa.md['bt_wavelength'],0.1812)
        self.assertEqual(self.sa.md['ex_name'],'myexp')
        self.assertEqual(self.sa.md['sa_name'],'my sample')
        uid1 = self.sa.md['sa_uid']
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml','sa_mysample.yml'])
        self.sa2 = Sample(' your sample',self.ex)
        self.assertEqual(self.sa2.md['sa_name'],'your sample')
        uid2 = self.sa2.md['sa_uid']
        self.assertNotEqual(uid1,uid2)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml','sa_mysample.yml','sa_yoursample.yml'])
        self.sa3 = Sample(' your sample',self.ex)
        self.assertEqual(self.sa3.md['sa_name'],'your sample')
        uid3 = self.sa3.md['sa_uid']
        self.assertEqual(uid2,uid3)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,['bt_bt.yml','ex_myexp.yml','sa_mysample.yml','sa_yoursample.yml'])

