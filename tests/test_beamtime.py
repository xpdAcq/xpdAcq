import unittest
import os
import shutil
from xpdacq.beamtimeSetup import _make_clean_env,_start_beamtime,_end_beamtime,_execute_start_beamtime,_check_empty_environment
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtime import XPD,Beamtime
from xpdacq.glbl import glbl
from xpdacq.beamtime import _clean_name,_clean_md_input,_update_objlist,_get_yaml_list,_get_hidden_list
from xpdacq.beamtime import *

class NewExptTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.config_dir = glbl.xpdconfig
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(self.config_dir):
            shutil.rmtree(self.config_dir)   
        os.makedirs(self.config_dir, exist_ok=True)
        self.PI_name = 'Billinge '
        self.saf_num = 234
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        self.saffile = os.path.join(self.config_dir,'saf{}.yml'.format(self.saf_num))
        #_make_clean_env()
        loadinfo = {'saf number':self.saf_num,'PI last name':self.PI_name,'experimenter list':self.experimenters}
        with open(self.saffile, 'w') as fo:
            yaml.dump(loadinfo,fo)
        self.bt = _start_beamtime(self.saf_num,home_dir=self.home_dir)     
        self.stbt_list = ['bt_bt.yml','ex_l-user.yml','sa_l-user.yml','sp_ct.1s.yml','sp_ct.5s.yml','sp_ct1s.yml','sp_ct5s.yml','sp_ct10s.yml','sp_ct30s.yml']

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
        self.assertEqual(newobjlist,self.stbt_list+['bt_test.yml'])
        xpdobj2 = XPD()
        xpdobj2.name = ' test2'
        xpdobj2.type = 'b t'
        testfname2 = os.path.join(yaml_dir,'bt_test2.yml')
        probe2 = xpdobj2._yamify()
        newobjlist2 = _get_yaml_list()
        self.assertEqual(newobjlist2,self.stbt_list+['bt_test.yml','bt_test2.yml'])
        self.assertEqual(probe,testfname)
        self.assertTrue(os.path.isfile(probe))
        # try adding another item that is already there
        probe3 = xpdobj2._yamify()
        newobjlist3 = _get_yaml_list()
        self.assertEqual(newobjlist3,self.stbt_list+['bt_test.yml','bt_test2.yml'])

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
        self.assertEqual(self.ex.md['bt_safN'],234)
        self.assertEqual(self.ex.md['bt_wavelength'],None)
        self.assertEqual(self.ex.md['ex_name'],'myexp')
        uid1 = self.ex.md['ex_uid']
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml'])
        self.ex2 = Experiment(' your exp',self.bt)
        self.assertEqual(self.ex2.md['ex_name'],'your exp')
        uid2 = self.ex2.md['ex_uid']
        self.assertNotEqual(uid1,uid2)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','ex_yourexp.yml'])
        self.ex3 = Experiment(' your exp',self.bt)
        self.assertEqual(self.ex3.md['ex_name'],'your exp')
        uid3 = self.ex3.md['ex_uid']
        self.assertEqual(uid2,uid3)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','ex_yourexp.yml'])

    def test_make_sample(self):
        name = 'my sample '
        self.ex = Experiment('myexp',self.bt)
        self.sa = Sample(name,self.ex)
        self.assertIsInstance(self.sa,Sample)
        self.assertEqual(self.sa.md['bt_experimenters'],[('van der Banerjee','S0ham',1),('Terban','Max',2)])
        self.assertEqual(self.sa.md['bt_piLast'],'Billinge')
        self.assertEqual(self.sa.md['bt_safN'],234)
        self.assertEqual(self.sa.md['bt_wavelength'],None)
        self.assertEqual(self.sa.md['ex_name'],'myexp')
        self.assertEqual(self.sa.md['sa_name'],'my sample')
        uid1 = self.sa.md['sa_uid']
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','sa_mysample.yml'])
        self.sa2 = Sample(' your sample',self.ex)
        self.assertEqual(self.sa2.md['sa_name'],'your sample')
        uid2 = self.sa2.md['sa_uid']
        self.assertNotEqual(uid1,uid2)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','sa_mysample.yml','sa_yoursample.yml'])
        self.sa3 = Sample(' your sample',self.ex)
        self.assertEqual(self.sa3.md['sa_name'],'your sample')
        uid3 = self.sa3.md['sa_uid']
        self.assertEqual(uid2,uid3)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','sa_mysample.yml','sa_yoursample.yml'])

    def test_make_scanPlan(self):
        self.sp = ScanPlan('myScan','ct',{'exposure':1.0})
        self.assertIsInstance(self.sp,ScanPlan)
        self.assertEqual(self.sp.md['sp_params'],{'exposure':1.0})
        uid1 = self.sp.md['sp_uid']
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['sp_myScan.yml'])
        self.sp2 = ScanPlan(' your scan','ct',{'exposure':1.0})
        self.assertEqual(self.sp2.md['sp_name'],'your scan')
        uid2 = self.sp2.md['sp_uid']
        self.assertNotEqual(uid1,uid2)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['sp_myScan.yml','sp_yourscan.yml'])
        self.sp3 = ScanPlan(' your scan','ct',{'exposure':1.0})
        self.assertEqual(self.sp3.md['sp_name'],'your scan')
        uid3 = self.sp3.md['sp_uid']
        self.assertEqual(uid2,uid3)
        # and one that fails the validator
        self.assertRaises(SystemExit,lambda: ScanPlan(' your scan','ct',{'exposur':1.0}))


    def test_hide(self):
        name = 'my sample '
        self.ex = Experiment('myexp',self.bt)
        self.sa = Sample(name,self.ex)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','sa_mysample.yml'])
        self.hidelist = self.bt.hide(1)
        self.assertEqual(self.hidelist,[1])
        hidden_list = _get_hidden_list() 
        self.assertEqual(self.hidelist,hidden_list)
  
    def test_unhide(self):
        name = 'my sample '
        self.ex = Experiment('myexp',self.bt)
        self.sa = Sample(name,self.ex)
        newobjlist = _get_yaml_list()
        self.assertEqual(newobjlist,self.stbt_list+['ex_myexp.yml','sa_mysample.yml'])
        self.hidelist = self.bt.hide(1)
        self.assertEqual(self.hidelist,[1])
        hidden_list1 = _get_hidden_list() 
        self.assertEqual(self.hidelist,hidden_list1)
        self.bt.unhide(0)
        hidden_list2 = _get_hidden_list() 
        self.assertEqual(hidden_list1,hidden_list2)
        self.bt.unhide(1)
        hidden_list3 = _get_hidden_list() 
        self.assertEqual(hidden_list3,[])

    def test_set_wavelength(self):
        wavelength = .18448
        self.bt = Beamtime('test',123)
        self.assertEqual(self.bt.md['bt_wavelength'],None)
        self.bt.set_wavelength(wavelength)
        self.assertEqual(self.bt.md['bt_wavelength'],wavelength)
        self.assertEqual(self.bt.name,'bt')
        self.assertEqual(self.bt.md['bt_piLast'],'test')
       
    def test_Scan_validator(self):
        #########################################################
        # Note: bt.list() so far is populated with l-user list
        #       bt.get(2) -> sa,'l-user' ; bt.get(5) -> sp, 'ct1s'
        #       bt.list() goes to 8
        ##########################################################
        # incorrect assignments -> str
        self.assertRaises(SystemExit, lambda: Scan._object_parser(Scan,'blahblah','sa'))
        self.assertRaises(SystemExit, lambda: Scan._object_parser(Scan,'ct157s','sp'))
        # incorrect assignments -> ind
        self.assertRaises(SystemExit, lambda: Scan._object_parser(Scan,100,'sp'))
        self.assertRaises(SystemExit, lambda: Scan._object_parser(Scan,250,'sa'))
        # incorrect object type from 3 kind of assignments
        self.assertRaises(TypeError, lambda: Scan(self.bt.get(1), self.bt.get(5))) # give Beamtime but not Sample
        self.assertRaises(TypeError, lambda: Scan(1, 'ct10s')) # give Beamtime but not Sample
        self.assertRaises(TypeError, lambda: Scan(8, 5)) # give two ScanPlan

    def test_auto_naming_ScanPlan(self):
        # wrong ScanPlan type
        self.assertRaises(SystemExit, lambda: ScanPlan('MRI_5_300_200_5'))
        # wrong positional arguments
        ''' doc string from ScanPlan
        expected format for each type is following:
        1) 'ct_10' means Count scan with 10s exposure time in total
        2) 'Tramp_10_300_200_5' means temperature ramp from 300k to 200k with 5k step and 10s exposure time each
        3) 'tseries_10_60_5' means time series scan of 10s exposure time each time 
            and run for 5 times with 60s delay between them.
        '''
        self.assertRaises(SystemExit, lambda: ScanPlan('ct_5_25575_32767')) # extra argument
        self.assertRaises(SystemExit, lambda: ScanPlan('Tramp_5_300_200')) # incomplete arguments
        self.assertRaises(SystemExit, lambda: ScanPlan('Tramp_5_300_200_5_1111')) # extra argument
        self.assertRaises(SystemExit, lambda: ScanPlan('tseries_5_60')) # incomplete arguments
        self.assertRaises(SystemExit, lambda: ScanPlan('tseries_5_60_10_1111')) # extra argument
        sp = ScanPlan('ct_5', shutter=False)
        self.assertEqual(sp.name, 'ct_5_nS')
        sp = ScanPlan('ct_5', shutter=True)
        self.assertEqual(sp.name, 'ct_5')
