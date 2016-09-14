import unittest
from unittest.mock import MagicMock
import os
import shutil
import time
import uuid
import yaml
import numpy as np
import copy
from xpdacq.glbl import glbl
from xpdacq.beamtime import Beamtime, Experiment, ScanPlan, Sample
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.xpdacq import _validate_dark, _yamify_dark, prun, _read_dark_yaml


class findRightDarkTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.config_dir = glbl.xpdconfig
        os.makedirs(self.config_dir, exist_ok=True)
        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee', 'S0ham', 1),
                              ('Terban ', ' Max', 2)]
        self.saffile = os.path.join(self.config_dir,
                                    'saf{}.yml'.format(self.saf_num))
        loadinfo = {'saf number': self.saf_num, 'PI last name': self.PI_name,
                    'experimenter list': self.experimenters}
        with open(self.saffile, 'w') as fo:
            yaml.dump(loadinfo, fo)
        self.bt = _start_beamtime(self.saf_num, home_dir=self.home_dir)
        self.stbt_list = ['bt_bt.yml', 'ex_l-user.yml', 'sa_l-user.yml',
                          'sc_ct.1s.yml', 'sc_ct.5s.yml', 'sc_ct1s.yml',
                          'sc_ct5s.yml', 'sc_ct10s.yml', 'sc_ct30s.yml']
        self.ex = Experiment('validateDark_unittest', self.bt)
        self.sa = Sample('unitttestSample', self.ex)

    def tearDown(self):
        os.chdir(glbl.base)
        if os.path.isdir(glbl.home):
            shutil.rmtree(glbl.home)
        if os.path.isdir(os.path.join(glbl.base, 'xpdConfig')):
            shutil.rmtree(os.path.join(glbl.base, 'xpdConfig'))

    def test_validate_dark_varying_exposure_and_expire_time(self):
        # extend case of test_qualified_dark. Iterate over different exposure_time and expire_time directly
        dark_scan_list, expire_time = [], 11.
        self.assertEqual(_validate_dark(0.1, expire_time, dark_scan_list),
                         None)
        time_now = time.time()
        dark_scan_list = []
        self.assertTrue(os.path.isfile(glbl.dk_yaml))
        for i in range(3):
            dark_def = (str(uuid.uuid1()), 0.1, time_now - 1200 + 600 * i)
            dark_scan_list.append(dark_def)
        # should return None if no valid items are found
        expire_time = 0.
        light_cnt_time = 0.1
        self.assertEqual(
            _validate_dark(light_cnt_time, expire_time, dark_scan_list), None)
        expire_time = 1000.
        light_cnt_time = 3.
        self.assertEqual(
            _validate_dark(light_cnt_time, expire_time, dark_scan_list), None)
        # find the most recent one
        dark_uid = dark_scan_list[-1][0]
        light_cnt_time = 0.1
        expire_time = 11.
        self.assertEqual(
            _validate_dark(light_cnt_time, expire_time, dark_scan_list),
            dark_uid)
        # should still find the most recent one, even though there is more than one valid one
        dark_uid = dark_scan_list[-1][0]
        expire_time = 22.
        self.assertEqual(
            _validate_dark(light_cnt_time, expire_time, dark_scan_list),
            dark_uid)
        # now find one that is in time but lower down the list because it has a different count time
        for i in range(3):
            dark_def = (
                str(uuid.uuid1()), 0.1 * (i + 1), time_now - 1200 + 600 * i)
            dark_scan_list.append(dark_def)
        test_list = copy.copy(dark_scan_list)
        dark_uid = dark_scan_list[-2][0]
        expire_time = 22.
        light_cnt_time = 0.2
        self.assertEqual(
            _validate_dark(light_cnt_time, expire_time, dark_scan_list),
            dark_uid)

    def test_dark_in_prun_can_find_a_valid_dark(self):
        # case 1: find a qualified dark and test if md got updated
        time_now = time.time()
        self.bt.set_wavelength(0.18448)
        light_cnt_time = 0.01

        dark_scan_list = []
        dark_uid = str(uuid.uuid4())
        dark_scan_list.append((dark_uid, light_cnt_time, time_now - 600))
        with open(glbl.dk_yaml, 'w') as f:
            yaml.dump(dark_scan_list, f)
        test_list = _read_dark_yaml()
        self.assertEqual(test_list, dark_scan_list)
        scanplan = ScanPlan('ct', {'exposure': light_cnt_time}, shutter=False)
        prun(self.sa, scanplan)
        self.assertTrue('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        self.assertTrue(
            glbl.xpdRE.call_args_list[-1][1]['sc_dk_field_uid'] == dark_uid)

    def test_dark_in_prun_cannot_find_a_valid_dark(self):
        # case 2: can't find a qualified dark and test if md got updated
        time_now = time.time()
        self.bt.set_wavelength(0.18448)
        # build the dark yml
        dark_scan_list = []
        dark_uid = str(uuid.uuid4())
        dark_uid2 = str(uuid.uuid4())
        dark_scan_list.append((dark_uid, 0.3, time_now - 2000))
        dark_scan_list.append((dark_uid2, 0.1, time_now - 200))
        with open(glbl.dk_yaml, 'w') as f:
            yaml.dump(dark_scan_list, f)
        test_list = _read_dark_yaml()
        self.assertEqual(test_list, dark_scan_list)
        # none with the right exposure
        scanplan = ScanPlan('ct', {'exposure': 0.01}, shutter=False)
        prun(self.sa, scanplan)
        self.assertTrue('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        self.assertFalse(
            glbl.xpdRE.call_args_list[-1][1]['sc_dk_field_uid'] == dark_uid2)
        # Second one has the right exposure time but expires
        glbl.dk_window = 1.
        scanplan = ScanPlan('ct', {'exposure': 0.1}, shutter=False)
        prun(self.sa, scanplan)
        self.assertTrue('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        self.assertFalse(
            glbl.xpdRE.call_args_list[-1][1]['sc_dk_field_uid'] == dark_uid2)

    def test_read_dark_yaml(self):
        # test if _read_dark_yaml captures exception as we hope
        self.assertTrue(os.path.isfile(
            glbl.dk_yaml))  # make sure it exit after _start_beamtime()
        os.remove(glbl.dk_yaml)
        self.assertRaises(SystemExit, lambda: _read_dark_yaml())
