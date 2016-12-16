"""module to test run_calibration"""
import os
import yaml
import shutil
import unittest

from xpdacq.glbl import glbl
from xpdacq.calib import (_configure_calib_instance,
                          _save_and_attach_calib_param,
                          _collect_calib_img,
                          _calibration)
from xpdacq.utils import import_sample_info
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.beamtimeSetup import _configure_devices, _start_beamtime


class calibTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir, 'xpdUser')
        self.config_dir = os.path.join(self.base_dir, 'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 300000  # must be 30000 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee', 'S0ham', 1),
                              ('Terban ', ' Max', 2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        xlf = '300000_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl.import_dir, xlf))
        import_sample_info(self.saf_num, self.bt)
        glbl.shutter_control = True
        self.xrun = CustomizedRunEngine(self.bt)
        # configure device
        _configure_devices(glbl)
        # link mds
        self.xrun.subscribe('all', glbl.db.mds.insert)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, 'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir, 'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir, 'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir, 'pe2_data'))

    def test_configure_calib(self):
        c = _configure_calib_instance(None, None, wavelength=None)
        # calibrant is None, which default to Ni
        self.assertEqual(c.calibrant.__repr__().split(' ')[0], 'Ni')
        # wavelength is None, so it should get the value from bt
        self.assertEqual(c.wavelength, self.bt.wavelength*10**(-10))
        # detector is None, which default to Perkin detector 
        self.assertEqual(c.detector.get_name(), 'Perkin detector')

        c2 = _configure_calib_instance(None, None, wavelength=999)
        # wavelength is given, so it should get customized value
        self.assertEqual(c2.wavelength, 999*10**(-10))

    
    def test_smoke_collect_calb_img(self):
        c = _configure_calib_instance(None, None, wavelength=None)
        _collect_calib_img(5.0, c, self.xrun)
        print(glbl.db[-1])
