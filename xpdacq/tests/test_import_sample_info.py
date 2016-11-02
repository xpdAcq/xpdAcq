import os
import yaml
import shutil
import unittest
from mock import MagicMock

from xpdacq.glbl import glbl
from xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime,
                                  load_beamtime)
from xpdacq.beamtime import (_summarize, ScanPlan, ct, Tramp, tseries,
                             Beamtime, Sample)
from xpdacq.utils import import_sample_info, _import_sample_info

# print messages for debugging
#xrun.msg_hook = print

class ImportSamplTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl['base']
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 300000  # must be 300000  => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),
                              ('Terban ',' Max',2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir,'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir,'pe2_data'))


    def test_import_sample_info_core_function(self):
        # no bt, default argument will fail
        self.assertRaises(TypeError, lambda: _import_sample_info(bt=None))
        # make bt but no spreadsheet
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        # expect FileNotFoundError as no spreadsheet
        self.assertRaises(FileNotFoundError,
                          lambda: _import_sample_info(bt=self.bt))
        # copy spreadsheet
        xlf = '300000_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl['import_dir'], xlf))

        # expect to pass with explicit argument
        _import_sample_info(300000, self.bt)
        # check imported sample metadata
        for sample in self.bt.samples.values():
            # Sample is a ChainMap with self.maps[1] == bt
            self.assertEqual(sample.maps[1], self.bt)

        # expect ValueError with inconsistent SAF_num between bt and input
        self.bt['bt_safN'] = 300179
        self.assertTrue(os.path.isfile(os.path.join(glbl['import_dir'],
                                                    xlf)))
        self.assertRaises(ValueError,
                          lambda: _import_sample_info(300000, self.bt))

        # expct TypeError with incorrect beamtime
        self.assertRaises(TypeError, lambda: _import_sample_info(bt=set()))
