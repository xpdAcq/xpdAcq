import unittest
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
from xpdacq.xpdacq import validate_dark, _yamify_dark, prun, _read_dark_yaml

shutter = glbl.shutter
shutter.put(1)

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


# this will be applied to test scan later
class ScanClassTest(unittest.TestCase): 
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

    def test_scan_calss(self):
        self.sp = ScanPlan('unittest_ScanPlan', 'ct', {'exposure':1.0})
        self.sc = Scan(self.sa, self.sp)
        sp_md_copy = copy.deepcopy(self.sp.md)
        # alternating md in sc and see if md in ScanPlan remain unchanged
        self.sc.md.update({'sc_isprun':True})
        self.assertEqual(self.sp.md, sp_md_copy)
        self.assertFalse('sc_isprun' in self.sp.md)
