import unittest
import os
import shutil
import yaml
import uuid
from configparser import ConfigParser
from time import strftime

# FIXME
from xpdacq.new_xpdacq.glbl import glbl
from xpdacq.new_xpdacq.beamtime import *
from xpdacq.new_xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime)
from xpdacq.new_xpdacq.xpdacq import (_validate_dark, CustomizedRunEngine,
                                      _auto_load_calibration_file)

class PrunTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = '123'   # must be 123 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        self.ex = Experiment('temp_test', self.bt)
        self.sp = ScanPlan(self.bt.experiments[0], ct, 10)
        self.sa = Sample('test_sample', self.bt, composition={'Ni':1})
        glbl.shutter_control = False

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir,'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir,'pe2_data'))

    def test_validate_dark(self):
        """ test login in this function """
        # no dark_dict_list
        self.assertFalse(glbl._dark_dict_list)
        rv = _validate_dark()
        self.assertEqual(rv, None)
        # initiate dark_dict_list
        # light cnt time is always 0.5 in mock detector, for now..
        dark_dict_list=[]
        now = time.time()

        # case1: adjust exposure time
        for i in range(5):
            dark_dict_list.append({'uid':str(uuid.uuid4()),
                                   'exposure':(i+1)*0.1,
                                   'timestamp':now,
                                   'acq_time':0.1})
        glbl._dark_dict_list = dark_dict_list
        correct_uid = [el['uid'] for el in dark_dict_list if
                       el['exposure'] == 0.5]
        self.assertEqual(len(correct_uid), 1)
        rv = _validate_dark()
        self.assertEqual(rv, correct_uid[-1])

        # case2: adjust expire time
        dark_dict_list = []
        for i in range(5):
            dark_dict_list.append({'uid':str(uuid.uuid4()),
                                   'exposure': 0.5,
                                   'timestamp':now-(i+1)*60,
                                   'acq_time':0.1})
        glbl._dark_dict_list = dark_dict_list
        correct_uid = [el['uid'] for el in dark_dict_list
                       if el['timestamp']- time.time() <=
                       (glbl.dk_window*60 -0.1)]
        # large window
        rv = _validate_dark()
        self.assertEqual(rv, correct_uid[-1])
        # small window
        rv = _validate_dark(0.1)
        self.assertEqual(rv, None)
        # medium window
        rv = _validate_dark(1.5)
        correct_uid = dark_dict_list[0]['uid']
        self.assertEqual(rv, correct_uid)

        # case3: adjust acqtime
        dark_dict_list = []
        for i in range(5):
            dark_dict_list.append({'uid':str(uuid.uuid4()),
                                   'exposure': 0.5,
                                   'timestamp':now,
                                   'acq_time':0.1*i})
        glbl._dark_dict_list = dark_dict_list
        correct_uid = [el['uid'] for el in dark_dict_list
                       if el['acq_time'] == glbl.frame_acq_time]
        rv = _validate_dark()
        self.assertEqual(len(correct_uid), 1)
        self.assertEqual(rv, correct_uid[-1])

        # case4: with real prun
        glbl.shutter_control = False # avoid waiting
        prun = CustomizedRunEngine(self.bt)
        prun_uid = prun(0,0)
        self.assertEqual(len(prun_uid),2) # first one is auto_dark
        rv = _validate_dark()
        self.assertEqual(prun_uid[0], rv)
        # no auto-dark
        glbl.auto_dark = False
        new_prun_uid = prun(0,0)
        self.assertEqual(len(new_prun_uid),1) # no dark frame
        self.assertEqual(glbl._dark_dict_list[-1]['uid'],  rv) # no update


    def test_auto_load_calibration(self):
        # no config file in xpdUser/config_base
        auto_calibration_md_dict = _auto_load_calibration_file()
        self.assertIsNone(auto_calibration_md_dict)
        # one config file in xpdUser/config_base:
        cfg_f_name = 'srxconfig.cfg'
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name)
        # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        config = ConfigParser()
        config.read(cfg_src)
        with open(cfg_dst, 'w') as f_original:
            config.write(f_original)
        #shutil.copy(cfg_src, cfg_dst)
        auto_calibration_md_dict = _auto_load_calibration_file()
        # is file loaded??
        self.assertTrue('parameters' in auto_calibration_md_dict)
        # is information loaded in correctly?
        self.assertEqual(auto_calibration_md_dict['parameters']['Experiment']
                         ['integrationspace'], 'qspace')
        self.assertEqual(auto_calibration_md_dict['parameters']['Others']
                         ['uncertaintyenable'], 'True')
        self.assertEqual(auto_calibration_md_dict['file_name'], cfg_f_name)
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
        modified_auto_calibration_md_dict = _auto_load_calibration_file()
        # is information loaded in correctly?
        self.assertEqual(modified_auto_calibration_md_dict
                         ['file_name'], modified_cfg_f_name)
        self.assertEqual(modified_auto_calibration_md_dict
                         ['parameters']['Others']['avgmask'],
                         'False')
