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


from xpdacq.utils import import_sample, excel_to_yaml


class ImportSampleTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir, 'xpdUser')
        self.config_dir = os.path.join(self.base_dir, 'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 30079
        # must be 30079 for proper config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee', 'S0ham', 1),
                              ('Terban ', ' Max', 2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        xlf = '30079_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl.xpdconfig, xlf))
        import_sample(self.saf_num, self.bt)

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, 'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir, 'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir, 'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir, 'pe2_data'))

    def test_phase_str_parser(self):
        # normal case
        test_str = 'TiO2:1, H2O:1, Ni:1'
        expect_result = ({'H': 0.66, 'O': 0.99, 'Ti': 0.33, 'Ni': 0.33},
                         {'TiO2': 0.33, 'H2O': 0.33, 'Ni': 0.33})
        rv = excel_to_yaml._phase_parser(test_str)
        self.assertEqual(rv[0], expect_result[0])
        self.assertEqual(rv[1], expect_result[1])
        # edge case: nothing follows ':'
        test_str = 'TiO2:, H2O:, Ni:1'
        expect_result = ({'H': 0.66, 'O': 0.99, 'Ti': 0.33, 'Ni': 0.33},
                         {'TiO2': 0.33, 'H2O': 0.33, 'Ni': 0.33})
        rv = excel_to_yaml._phase_parser(test_str)
        self.assertEqual(rv[0], expect_result[0])
        self.assertEqual(rv[1], expect_result[1])
        # edge case: ':' not in str, non alpha numeric symbols instead
        test_str = 'TiO2;, H2O:, Ni^1'
        expect_result = ({'H': 0.66, 'O': 0.99, 'Ti': 0.33, 'Ni': 0.33},
                         {'TiO2': 0.33, 'H2O': 0.33, 'Ni': 0.33})
        rv = excel_to_yaml._phase_parser(test_str)
        self.assertEqual(rv[0], expect_result[0])
        self.assertEqual(rv[1], expect_result[1])
        # edge case: not comma separated -> ValueError
        test_str = 'TiO2; H2O: Ni^1'
        self.assertRaises(ValueError,
                          lambda: excel_to_yaml._phase_parser(test_str))

    def test_comma_separate_parser(self):
        # normal case
        test_str = 'New Order, Joy Division, Smashing Pumpkins'
        expect_result = ['New Order', 'Joy Division',
                         'Smashing Pumpkins']
        rv = excel_to_yaml._comma_separate_parser(test_str)
        self.assertEqual(rv, expect_result)
        # no comma -> whole str as list
        test_str = 'New Order Joy Division Smashing Pumpkins      '
        self.assertEqual([test_str.strip()],
                         excel_to_yaml._comma_separate_parser(test_str))

    def test_name_parser(self):
        # normal case
        test_str = 'New Order, Joy Division, Smashing Pumpkins'
        expect_result = ['New', 'Order', 'Joy', 'Division',
                         'Smashing', 'Pumpkins']
        name_list = []
        parsed_list = excel_to_yaml._comma_separate_parser(test_str)
        for el in parsed_list:
            name_list.extend(excel_to_yaml._name_parser(el))
        self.assertEqual(name_list, expect_result)
        # edge case: no comma between firt and last, still can parse
        test_str = 'New Order Joy Division Smashing Pumpkins'
        expect_result = ['New', 'Order', 'Joy', 'Division',
                         'Smashing', 'Pumpkins']
        name_list = []
        parsed_list = excel_to_yaml._comma_separate_parser(test_str)
        for el in parsed_list:
            name_list.extend(excel_to_yaml._name_parser(el))
        self.assertEqual(name_list, expect_result)
