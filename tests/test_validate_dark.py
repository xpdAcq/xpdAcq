import unittest
import os
import shutil
import time
import uuid
import yaml
import numpy as np
#from xpdacq.xpdacq import _areaDET
#from xpdacq.xpdacq import _tempController
#from xpdacq.xpdacq import _shutter
#from xpdacq.xpdacq import _bdir
#from xpdacq.xpdacq import _cdir
#from xpdacq.xpdacq import _hdir
#from xpdacq.xpdacq import _hostname
from xpdacq.glbl import glbl
from xpdacq.xpdacq import validate_dark, _qualified_dark, _yamify_dark, _unittest_prun
from xpdacq.beamtime import Beamtime, Experiment, ScanPlan, Sample

class findRightDarkTest(unittest.TestCase): 

    def setUp(self):
        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        self.bt = Beamtime(self.PI_name, self.saf_num, self.wavelength, self.experimenters)
        self.ex = Experiment('unittestExperiment', self.bt)
        self.sa = Sample('unittestSample', self.ex)
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
     
    def test_qualified_dark_v1(self):
        # case 1: all dark are not expired. Iterate over differnt exposure time
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,5):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)
        expire_time = 1. # interms of minute
        for i in range(1,5):
            info_tuple = list(dark_scan_list[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            expect_list = []
            expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, i*0.1, expire_time))
    
    def test_qualified_dark_v2(self):
        # case 2: all dark have the same exposure time but differnt timestamp. Iterate over differnt expire time
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(0.2): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)
        for i in range(1,3):
            expire_time = i * 0.1
            expect_length = i
            self.assertEqual(expect_length, len(_qualified_dark(dark_scan_list, 0.2, expire_time)))
            # length of qualified dark index should grow
 
    def test_qualified_dark_v3(self):
        # case 3: Iterate over differnt exposure_time and different expire_time
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(0.1*i): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)

        for i in range(1,3):
            expire_time = i*0.2 # in terms of minute
            light_cnt_time = i*0.1
            expect_list = []
            expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, light_cnt_time, expire_time))
    
    def test_qualified_dark_v4(self):
        # case 4: can't find any qualified dark
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(0.1*i): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)

        for i in range(1,3):
            expire_time = i*0.2 # in terms of minute
            light_cnt_time = i*0.1 + (np.random.randn()+2)
            expect_list = []
            #expect_list.append(i-1)
            self.assertEqual(expect_list, _qualified_dark(dark_scan_list, light_cnt_time, expire_time))

    def test_validate_dark(self):
        # extend case of test_qualified_dark. Iterate over different exposure_time and expire_time directly
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(0.1*i): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)

        for i in range(1,3):
            expire_time = i*0.2
            info_tuple = list(dark_scan_list[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            self.assertEqual(validate_dark(i*0.1, expire_time), dark_uid)
    
    def test_update_md_v1(self):
        # case 1: find a qualified dark and test if md got updated
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)

        for i in range(1,3):
            scan = ScanPlan('ctTest', 'ct', {'exposure':0.1*i})
            info_tuple = list(dark_scan_list[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            self.assertEqual(_unittest_prun(self.sa, scan)['sc_params']['dk_field_uid'], dark_uid)

    def test_update_md_v2(self):
        # case 2: can't find a qualified dark
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(1,3):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            _yamify_dark(dark_def)
            time.sleep(5)
        with open(glbl.dk_yaml, 'r') as f:
            dark_scan_list = yaml.load(f)
                
        for i in range(1,3):
            scan = ScanPlan('ctTest', 'ct', {'exposure':0.1*i + (np.random.randn()+2)})
            info_tuple = list(dark_scan_list[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            self.assertEqual(_unittest_prun(self.sa, scan)['sc_params']['dk_field_uid'], 'can not find a qualified dark uid')

