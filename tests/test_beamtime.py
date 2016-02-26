import unittest
import os
import shutil
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtime import XPD
from xpdacq.glbl import glbl
from xpdacq.beamtime import _clean_name

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
    def test_list(self):
        self.fail('need a test for list')
    
#    @unittest.skip('skipping yaml list')
#    def test_get_yaml_list(self):
#    	xpdobj = XPD()
#    	yaml_dir = glbl.yaml_dir
#        # create a yaml list yml file
#    	lname = os.path.join(yaml_dir,'_acqobj_list.yml')
#        open(lname, 'w').close()
#        # now get the list of yamls.
#    	olist = xpdobj._get_yaml_list()
#        assertEqual(olist,[os.path.join(yaml_dir,'bt_b.yml')])
#        #self.fail('need a test for list')

    @unittest.expectedFailure
    def test_loadyamls(self):
        self.fail('need a test for list')

    def test_yamify(self):
        xpdobj = XPD()
        xpdobj.name = ' test'
        xpdobj.type = 'b t'
        yaml_dir = xpdobj._yaml_path()
        testfname = os.path.join(yaml_dir,'bt_test.yml')
        XPD.objlist = []
        probe = xpdobj._yamify()
        self.assertEqual(XPD.objlist,['bt_test.yml'])
        xpdobj2 = XPD()
        xpdobj2.name = ' test2'
        xpdobj2.type = 'b t'
        yaml_dir = xpdobj2._yaml_path()
        testfname2 = os.path.join(yaml_dir,'bt_test2.yml')
        probe2 = xpdobj2._yamify()
        self.assertEqual(XPD.objlist,['bt_test.yml','bt_test2.yml'])

        self.assertEqual(probe,testfname)
        self.assertTrue(os.path.isfile(probe))
#        olist = xpdobj.loadyamls()
#        self.assertEqual(olist[0].name,'bt')
#        self.assertEqual(olist[0].type,'bt')

    def test_update_objlist(self):
        xpdobj = XPD()
        XPD.objlist = []
        xpdobj._update_objlist('testme')
        self.assertEqual(xpdobj.objlist,['testme'])

