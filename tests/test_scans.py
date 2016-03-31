import unittest
from unittest.mock import MagicMock, patch
import os
from configparser import ConfigParser
import shutil
import time
import uuid
import yaml
import numpy as np
import copy
from xpdacq.glbl import glbl
from xpdacq.beamtime import Beamtime, Experiment, ScanPlan, Sample, Scan
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.xpdacq import prun, calibration, dark, _auto_dark_collection, _auto_load_calibration_file
from xpdacq.control import _open_shutter, _close_shutter

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

def ideal_prun(sample, scanplan, **kwargs):
    ''' a note to remind myself '''
    scan = Scan(samplm, scanplan)
    scan.md.update({'sc_isprun':True})
    _executes_scan(scan)
    return

class NewScanTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = glbl.home
        self.config_dir = glbl.xpdconfig
        os.makedirs(self.config_dir, exist_ok=True)
        #os.makedirs(glbl.yaml_dir, exist_ok = True)
        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        self.saffile = os.path.join(self.config_dir,'saf{}.yml'.format(self.saf_num))
        loadinfo = {'saf number':self.saf_num,'PI last name':self.PI_name,'experimenter list':self.experimenters}
        with open(self.saffile, 'w') as fo:
            yaml.dump(loadinfo,fo)
        self.bt = _start_beamtime(self.saf_num,home_dir=self.home_dir)
        self.stbt_list = ['bt_bt.yml','ex_l-user.yml','sa_l-user.yml','sp_ct.1s.yml','sp_ct.5s.yml','sp_ct1s.yml','sp_ct5s.yml','sp_ct10s.yml','sp_ct30s.yml']
        self.ex = Experiment('validateDark_unittest', self.bt)
        self.sa = Sample('unitttestSample', self.ex)

    def tearDown(self):
        os.chdir(glbl.base)
        if os.path.isdir(glbl.home):
            shutil.rmtree(glbl.home)
        if os.path.isdir(os.path.join(glbl.base,'xpdConfig')):
            shutil.rmtree(os.path.join(glbl.base,'xpdConfig'))

    def test_auto_dark_collection(self):
        self.sp_set_dk_window = ScanPlan('unittest_count','ct', {'exposure': 0.1, 'dk_window':25575}, shutter = False)
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        self.sc_set_dk_window = Scan(self.sa, self.sp_set_dk_window)
        self.sc = Scan(self.sa, self.sp)
        auto_dark_md_dict_set_dk_window = _auto_dark_collection(self.sc_set_dk_window)
        auto_dark_md_dict = _auto_dark_collection(self.sc)
        # test if md is updated
        self.assertTrue('sc_dk_field_uid' in auto_dark_md_dict_set_dk_window and 'sc_dk_field_uid' in auto_dark_md_dict)
        # test if dk_window is overwrittten
        self.assertEqual(glbl.dk_window, auto_dark_md_dict['sc_dk_window'])
        self.assertEqual(25575, auto_dark_md_dict_set_dk_window['sc_dk_window'])

    def test_auto_load_calibration(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        # no config file in xpdUser/config_base
        auto_calibration_md_dict = _auto_load_calibration_file()
        self.assertIsNone(auto_calibration_md_dict)
        # one config file in xpdUser/config_base:
        cfg_f_name = 'srxconfig.cfg'
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name) # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        config = ConfigParser()
        config.read(cfg_src)
        with open(cfg_dst, 'w') as f_original:
            config.write(f_original)
        #shutil.copy(cfg_src, cfg_dst)
        auto_calibration_md_dict = _auto_load_calibration_file()
        # is file loaded??
        self.assertTrue('sc_calibration_parameters' in auto_calibration_md_dict)
        # is information loaded in correctly?
        self.assertEqual(auto_calibration_md_dict['sc_calibration_parameters']['Experiment']['integrationspace'], 'qspace')
        self.assertEqual(auto_calibration_md_dict['sc_calibration_parameters']['Others']['uncertaintyenable'], 'True')
        self.assertEqual(auto_calibration_md_dict['sc_calibration_file_name'], cfg_f_name)
        # multiple config files in xpdUser/config_base:
        self.assertTrue(os.path.isfile(cfg_dst))
        modified_cfg_f_name = 'srxconfig_1.cfg'
        modified_cfg_dst = os.path.join(glbl.config_base, modified_cfg_f_name)
        config = ConfigParser()
        config.read(cfg_src)
        config['Others']['avgmask'] = 'False'
        with open(modified_cfg_dst, 'w') as f_modified:
            config.write(f_modified)
        self.assertTrue(os.path.isfile(modified_cfg_dst))
        #modified_cfg_src = os.path.join(os.path.dirname(__file__), modified_cfg_f_name)
        #shutil.copy(modified_cfg_src, modified_cfg_dst)
        modified_auto_calibration_md_dict = _auto_load_calibration_file()
        # is information loaded in correctly?
        #debug = list(map(lambda x: os.path.getmtime(x), os.listdir(glbl.config_base)))
        #print(debug)
        self.assertEqual(modified_auto_calibration_md_dict['sc_calibration_file_name'], modified_cfg_f_name)
        self.assertEqual(modified_auto_calibration_md_dict['sc_calibration_parameters']['Others']['avgmask'], 'False')

    def test_new_prun_with_auto_dark_and_auto_calibration(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1, 'dk_window':32767}, shutter = False)
        self.sc = Scan(self.sa, self.sp)
        self.assertEqual(self.sc.sp, self.sp)
        cfg_f_name = 'srxconfig.cfg'
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name) # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        prun(self.sa, self.sp)
        # is xpdRE used?
        self.assertTrue(glbl.xpdRE.called)
        # is md updated?
        self.assertFalse(glbl.xpdRE.call_args_list[-1][1] == self.sc.md)
        # is prun passed eventually?
        self.assertTrue('sc_isprun' in glbl.xpdRE.call_args_list[-1][1])
        # is auto_dark executed?
        self.assertTrue('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        # is dk_window changed as ScanPlan object changed??
        self.assertEqual(glbl.xpdRE.call_args_list[-1][1]['sc_dk_window'], 32767)
        # is calibration loaded?
        self.assertEqual(glbl.xpdRE.call_args_list[-1][1]['sc_calibration_file_name'], cfg_f_name)
        # is  ScanPlan.md remain unchanged after scan?
        self.assertFalse('sc_isprun' in self.sp.md)

    def test_new_prun_no_auto_dark_but_auto_calibration(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1, 'dk_window':32767}, shutter = False)
        self.sc = Scan(self.sa, self.sp)
        self.assertEqual(self.sc.sp, self.sp)
        cfg_f_name = 'srxconfig.cfg'
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name) # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        prun(self.sa, self.sp, auto_dark = False)
        # is xpdRE used?
        self.assertTrue(glbl.xpdRE.called)
        # is md updated?
        self.assertFalse(glbl.xpdRE.call_args_list[-1][1] == self.sc.md)
        # is prun passed eventually?
        self.assertTrue('sc_isprun' in glbl.xpdRE.call_args_list[-1][1])
        # is auto_dark executed? -> No
        self.assertFalse('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        # is calibration loaded?
        self.assertTrue(cfg_f_name in glbl.xpdRE.call_args_list[-1][1]['sc_calibration_file_name'])
        # is  ScanPlan.md remain unchanged after scan?
        self.assertFalse('sc_isprun' in self.sp.md)

    def test_dark(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        self.sc = Scan(self.sa, self.sp)
        self.assertEqual(self.sc.sp, self.sp)
        cfg_f_name = 'srxconfig.cfg'
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name) # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        dark(self.sa, self.sp)
        # is xpdRE used?
        self.assertTrue(glbl.xpdRE.called)
        # is md updated?
        self.assertFalse(glbl.xpdRE.call_args_list[-1][1] == self.sc.md)
        # is dark labeled eventually?
        self.assertTrue('sc_isdark' in glbl.xpdRE.call_args_list[-1][1])
        # is auto_dark executed? -> No
        self.assertFalse('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        # is calibration loaded? -> No
        self.assertFalse('sc_calibration_file_name' in glbl.xpdRE.call_args_list[-1][1])
        # is  ScanPlan.md remain unchanged after scan?
        self.assertFalse('sc_isdark' in self.sp.md)

    def test_calibration(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        self.sc = Scan(self.sa, self.sp)
        self.assertEqual(self.sc.sp, self.sp)
        calibration(self.sa, self.sp)
        # is xpdRE used?
        self.assertTrue(glbl.xpdRE.called)
        # is md updated?
        self.assertFalse(glbl.xpdRE.call_args_list[-1][1] == self.sc.md)
        # is calibration labeled eventually?
        self.assertTrue('sc_iscalibration' in glbl.xpdRE.call_args_list[-1][1])
        # is auto_dark executed?
        self.assertTrue('sc_dk_field_uid' in glbl.xpdRE.call_args_list[-1][1])
        # is calibration loaded? -> No
        self.assertFalse('sc_calibration_file_name' in glbl.xpdRE.call_args_list[-1][1])
        # is  ScanPlan.md remain unchanged after scan?
        self.assertFalse('sc_iscalibration' in self.sp.md)
