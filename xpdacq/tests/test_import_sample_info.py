import os
import yaml
import shutil
import warnings
import unittest
from pkg_resources import resource_filename as rs_fn

from xpdacq.glbl import glbl
from xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime,
                                  load_beamtime)
from xpdacq.beamtime import (_summarize, ScanPlan, ct, Tramp, tseries,
                             Beamtime, Sample)
from xpdacq.utils import import_sample_info, _import_sample_info


# print messages for debugging
# xrun.msg_hook = print

class ImportSamplTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl['base']
        self.home_dir = os.path.join(self.base_dir, 'xpdUser')
        self.config_dir = os.path.join(self.base_dir, 'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 300000  # must be 300000  => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee', 'S0ham', 1),
                              ('Terban ', ' Max', 2)]
        self.pkg_rs = rs_fn('xpdacq', 'examples/')
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, 'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir, 'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir, 'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir, 'pe2_data'))

    def test_import_sample_info_core_function(self):
        # no bt, default argument will fail
        self.assertRaises(TypeError, lambda: _import_sample_info(bt=None))
        # make bt but no spreadsheet
        pytest_dir = rs_fn('xpdacq', 'tests/')
        config = 'XPD_beamline_config.yml'
        configsrc = os.path.join(pytest_dir, config)
        shutil.copyfile(configsrc, os.path.join(self.config_dir, config))
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength, test=True)
        # expect FileNotFoundError as no spreadsheet
        xlf = '300000_sample.xlsx'
        self.assertFalse(os.path.isfile(os.path.join(glbl['import_dir'],
                                                     xlf)))
        self.assertRaises(FileNotFoundError,
                          lambda: _import_sample_info(bt=self.bt))
        # copy spreadsheet
        xlf = '300000_sample.xlsx'
        src = os.path.join(self.pkg_rs, xlf)
        shutil.copyfile(src, os.path.join(glbl['import_dir'], xlf))
        # problematic ones
        xlf2 = '999999_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf2)
        shutil.copyfile(src, os.path.join(glbl['import_dir'], xlf2))
        # test with ordinary import
        # expect to pass with explicit argument
        _import_sample_info(300000, self.bt)
        # check imported sample metadata
        for sample in self.bt.samples.values():
            # Sample is a ChainMap with self.maps[1] == bt
            self.assertEqual(sample.maps[1], self.bt)

        # expect ValueError with inconsistent SAF_num between bt and input
        self.bt['bt_safN'] = str(300179)
        self.assertTrue(os.path.isfile(os.path.join(glbl['import_dir'],
                                                    xlf)))
        self.assertRaises(ValueError,
                          lambda: _import_sample_info(300000, self.bt))

        # expct TypeError with incorrect beamtime
        self.assertRaises(TypeError, lambda: _import_sample_info(bt=set()))
        # error when validate the md
        self.bt['bt_safN'] = str(999999)
        self.assertRaises(RuntimeError,
                          lambda: _import_sample_info(999999, self.bt,
                                                      validate_only=True))
        # test get_md_method
        sample_obj_list = [el for el in self.bt.samples.values()]
        for i, el in enumerate(sample_obj_list):
            self.assertEqual(dict(el), self.bt.samples.get_md(i))
