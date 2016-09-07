import unittest
import os
import shutil
import yaml
import uuid
from configparser import ConfigParser
from time import strftime

from xpdacq.glbl import glbl
from xpdacq.beamtime import *
from xpdacq.utils import import_sample
from xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime)
from xpdacq.xpdacq import (_validate_dark, CustomizedRunEngine,
                           _auto_load_calibration_file,
                           open_collection)

class PrunTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 30079   # must be 30079 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),
                              ('Terban ',' Max',2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        xlf = '30079_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl.xpdconfig, xlf))
        import_sample(self.saf_num, self.bt)
        self.sp = ScanPlan(self.bt, ct, 5)
        glbl.shutter_control = False
        self.prun = CustomizedRunEngine(self.bt)
        open_collection('unittest')

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
        if glbl._dark_dict_list:
            glbl._dark_dict_list = []
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
        glbl._dark_dict_list = [] # re-init
        prun_uid = self.prun(0,0)
        self.assertEqual(len(prun_uid),2) # first one is auto_dark
        dark_uid = _validate_dark()
        self.assertEqual(prun_uid[0], dark_uid)
        # test sc_dark_field_uid
        msg_list = []
        def msg_rv(msg):
            msg_list.append(msg)
        self.prun.msg_hook = msg_rv
        self.prun(0,0)
        open_run = [el.kwargs for el in msg_list if el.command=='open_run'][0]
        self.assertEqual(dark_uid, open_run['sc_dk_field_uid'])
        # no auto-dark
        glbl.auto_dark = False
        new_prun_uid = self.prun(0,0)
        self.assertEqual(len(new_prun_uid),1) # no dark frame
        self.assertEqual(glbl._dark_dict_list[-1]['uid'],  dark_uid) # no update


    def test_auto_load_calibration(self):
        # no config file in xpdUser/config_base
        auto_calibration_md_dict = _auto_load_calibration_file()
        self.assertIsNone(auto_calibration_md_dict)
        # one config file in xpdUser/config_base:
        cfg_f_name = glbl.calib_config_name
        cfg_src = os.path.join(os.path.dirname(__file__), cfg_f_name)
        # __file__ gives relative path
        cfg_dst = os.path.join(glbl.config_base, cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        with open(cfg_dst) as f:
            config_from_file = yaml.load(f)
        glbl.calib_config_dict = config_from_file
        auto_calibration_md_dict = _auto_load_calibration_file()
        # is file loaded??
        self.assertTrue('time' in auto_calibration_md_dict)
        # is information loaded in correctly?
        self.assertEqual(auto_calibration_md_dict['pixel2'],
                         0.0002)
        self.assertEqual(auto_calibration_md_dict['file_name'],
                         'pyFAI_calib_Ni_20160813-1659.poni')
        # file-based config_dict is different from glbl.calib_config_dict
        self.assertTrue(os.path.isfile(cfg_dst))
        glbl.calib_config_dict = dict(auto_calibration_md_dict)
        glbl.calib_config_dict['new_filed']='i am new'
        re_auto_calibration_md_dict = _auto_load_calibration_file()
        # trust file-based config_dict
        self.assertEqual(re_auto_calibration_md_dict, config_from_file)
        self.assertFalse('new_field' in re_auto_calibration_md_dict)
        # test with prun
        msg_list = []
        def msg_rv(msg):
            msg_list.append(msg)
        self.prun.msg_hook = msg_rv
        prun_uid = self.prun(0,0)
        open_run = [el.kwargs for el in msg_list
                    if el.command=='open_run'][0]
        self.assertTrue('sc_calibration_md' in open_run)
        self.assertEqual(open_run['sc_calibration_md'],
                         re_auto_calibration_md_dict)

    def test_open_collection(self):
        # no collection
        delattr(glbl,'collection')
        self.assertRaises(RuntimeError, lambda: self.prun(0,0))
        # test collection num
        open_collection('unittest_collection')
        self.assertEqual(glbl.collection, [])
        self.prun(0,0)
        self.assertEqual(glbl.collection_num, 1)
