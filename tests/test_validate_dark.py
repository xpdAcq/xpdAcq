import unittest
import os
import shutil
import time
import uuid
import yaml
import numpy as np
from xpdacq.glbl import glbl
from xpdacq.glbl import _areaDET, _tempController
from xpdacq.glbl import _shutter, _verify_write
from xpdacq.glbl import _LiveTable
from xpdacq.beamtime import Beamtime, Experiment, ScanPlan, Sample
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
_areaDET()
_tempController()
_shutter()
_verify_write()
_LiveTable()
from xpdacq.xpdacq import validate_dark,  _yamify_dark 


# this is here temporarily.  Simon wanted it out of the production code.  Needs to be refactored.
# the issue is to mock RE properly.  This is basically prun without the call to RE which
# isn't properly mocked yet.
def _unittest_prun(sample,scan,**kwargs):
    '''on this 'sample' run this 'scan'
    
    this function doesn't control shutter nor trigger run engine. It is designed to test functionality

    Arguments:
    sample - sample metadata object
    scan - scan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    scan.md.update({'xp_isprun':True})
    light_cnt_time = scan.md['sc_params']['exposure']
    expire_time = glbl.dk_window
    dark_field_uid = validate_dark(light_cnt_time, expire_time)
    if not dark_field_uid: dark_field_uid = 'can not find a qualified dark uid'
    scan.md['sc_params'].update({'dk_field_uid': dark_field_uid})
    scan.md['sc_params'].update({'dk_window':expire_time})
    return scan.md


class findRightDarkTest(unittest.TestCase): 
    def setUp(self):
        #os.makedirs(glbl.yaml_dir, exist_ok = True)
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.config_dir = glbl.xpdconfig
        #os.makedirs(self.config_dir, exist_ok=True)
        self.PI_name = 'Billinge '
        self.saf_num = 234
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        #self.bt = _start_beamtime(self.saf_num,home_dir=self.home_dir) 
        self.saffile = os.path.join(self.config_dir,'saf{}.yml'.format(self.saf_num))
        loadinfo = {'saf number':self.saf_num,'PI last name':self.PI_name,'experimenter list':self.experimenters}
        with open(self.saffile, 'w') as fo:
            yaml.dump(loadinfo,fo)
        self.bt = _start_beamtime(self.saf_num,home_dir=self.home_dir)     
        self.stbt_list = ['bt_bt.yml','ex_l-user.yml','sa_l-user.yml','sc_ct.1s.yml','sc_ct.5s.yml','sc_ct1s.yml','sc_ct5s.yml','sc_ct10s.yml','sc_ct30s.yml']
        self.ex = Experiment('validateDark_unittest', self.bt)
        self.sa = Sample('unitttestSample', self.ex)

        
        os.makedirs(glbl.yaml_dir, exist_ok = True)
        # initiate dark_scan_list
        self.dark_scan_list = []
        with open (glbl.dk_yaml, 'w') as f:
            yaml.dump(self.dark_scan_list, f)
                
    def tearDown(self):
        os.chdir(glbl.base)
        if os.path.isdir(glbl.home):
            shutil.rmtree(glbl.home)
        if os.path.isdir(os.path.join(glbl.base,'xpdConfig')):
            shutil.rmtree(os.path.join(glbl.base,'xpdConfig'))

    @unittest.skip('')
    def test_qualified_dark_with_varying_exposure_time(self):
        # case 1: all dark are not expired. Iterate over differnt exposure time
        time_now = time.time()
        dark_scan_list = []
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        for i in range(1,5):
            dark_def = (str(uuid.uuid1()), i*0.1, time_now)
            dark_scan_list.append(dark_def)

        expire_time = 1. # interms of minute
        for i in range(1,5):
#            expire_time = i*11. # in terms of minute
            light_cnt_time = i*0.1
            expect_list = []
            expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, i*0.1, expire_time))
    
    @unittest.skip('')
    def test_qualified_dark_varying_expire_time(self):
        # case 2: all dark have the same exposure time but differnt timestamp. Iterate over differnt expire time
        time_now = time.time()
        dark_scan_list = []
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.2, time_now-600*(i))
            dark_scan_list.append(dark_def)
        expire_time = 9.
        expect_length = 0
        self.assertEqual(expect_length, len(_qualified_dark(dark_scan_list, 0.2, expire_time)))
        expire_time = 12.
        expect_length = 1
        self.assertEqual(expect_length, len(_qualified_dark(dark_scan_list, 0.2, expire_time)))
        expire_time = 22.
        expect_length = 2
        self.assertEqual(expect_length, len(_qualified_dark(dark_scan_list, 0.2, expire_time)))
            # length of qualified dark index should grow

    @unittest.skip('')
    def test_qualified_dark_varying_expire_and_exposure_time(self):
        # case 3: Iterate over differnt exposure_time and different expire_time
        time_now = time.time()
        dark_scan_list = []
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.1*i, time_now-600*(i))
            dark_scan_list.append(dark_def)

        for i in range(1,3):
            expire_time = i*11. # in terms of minute
            light_cnt_time = i*0.1
            expect_list = []
            expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, light_cnt_time, expire_time))
    
    @unittest.skip('')
    def test_qualified_dark_with_no_matched_dark(self):
        # case 4: can't find any qualified dark
        time_now = time.time()
        dark_scan_list = []
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.1*i, time_now-600*(i))
            dark_scan_list.append(dark_def)

        for i in range(1,3):
            expire_time = i*11. # in terms of minute
            light_cnt_time = i*0.1 + 2.
            expect_list = []
            #expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, light_cnt_time, expire_time))

    def test_validate_dark_varying_exposure_and_expire_time(self):
        # extend case of test_qualified_dark. Iterate over different exposure_time and expire_time directly
        time_now = time.time()
        dark_scan_list = []
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.1, time_now-1200+600*(i-1))
            dark_scan_list.append(dark_def)
        # should return None if no valid items are found
        expire_time = 0.
        light_cnt_time = 0.1
        self.assertEqual(validate_dark(light_cnt_time, expire_time,dark_scan_list), None)
        dark_uid = dark_def[0]
        expire_time = 11.
        self.assertEqual(validate_dark(light_cnt_time, expire_time,dark_scan_list), dark_uid)


    @unittest.skip('skipping test with prun.  Need to refactor prun to take a dk_expiration_time optional variable?')
    def test_prun_varying_exposure_and_expire_time(self):
        # case 1: find a qualified dark and test if md got updated
        time_now = time.time()
        dark_scan_list = []
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.1*i, time_now-600*(i))
            dark_scan_list.append(dark_def)

        for i in range(1,3):
            expire_time = i*11.
            dark_scan_info = dark_scan_list[i-1]
            dark_uid = list(dark_scan_info.values())[0][0]
            scan = ScanPlan('ctTest', 'ct', {'exposure':0.1*i})
            self.assertEqual(_unittest_prun(self.sa, scan)['sc_params']['dk_field_uid'], dark_uid)

    @unittest.skip("need this without the sleep. This test doesn't test anything right now.")
    def test_prun_with_no_matched_dark(self):
        # case 2: can't find a qualified dark
        time_now = time.time()
        dark_scan_list = []
        from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = (str(uuid.uuid1()), 0.1*i, time_now-600*(i))
            dark_scan_list.append(dark_def)

        for i in range(1,3):
            scan = ScanPlan('ctTest', 'ct', {'exposure':0.1*i + (np.random.randn()+2)})
            info_tuple = list(dark_scan_list[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            self.assertEqual(_unittest_prun(self.sa, scan)['sc_params']['dk_field_uid'], 'can not find a qualified dark uid')
