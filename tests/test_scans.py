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
from xpdacq.beamtime import Beamtime, Experiment, ScanPlan, Sample, Scan
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.xpdacq import prun, _auto_dark
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
    
class findRightDarkTest(unittest.TestCase): 
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
    
    def test_current_prun(self):
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        self.sc = Scan(self.sa, self.sp)
        self.assertEqual(self.sc.sp, self.sp)
        prun(self.sa, self.sp)
        self.assertFalse('sc_isprun' in self.sp.md) # after prun buch of md should be updated
        #self.assertEqual((), glbl.xpdRE.count_args[1]) # in interactive shell, that works but not in module

    def test_auto_dark(self):
        self.sp_set_dk_window = ScanPlan('unittest_count','ct', {'exposure': 0.1, 'dk_window':25575}, shutter = False)
        self.sp = ScanPlan('unittest_count','ct', {'exposure': 0.1}, shutter = False)
        self.sc_set_dk_window = Scan(self.sa, self.sp_set_dk_window)
        self.sc = Scan(self.sa, self.sp)
        auto_dark_md_dict_set_dk_window = _auto_dark(self.sc_set_dk_window)
        auto_dark_md_dict = _auto_dark(self.sc)
        self.assertTrue('sc_dk_field_uid' in auto_dark_md_dict_set_dk_window and 'sc_dk_field_uid' in auto_dark_md_dict)
        self.assertTrue('sc_dk_window' in auto_dark_md_dict_set_dk_window and 'sc_dk_window' in auto_dark_md_dict)
        self.assertEqual(glbl.dk_window, auto_dark_md_dict['sc_dk_window'])
        self.assertEqual(25575, auto_dark_md_dict_set_dk_window['sc_dk_window'])
