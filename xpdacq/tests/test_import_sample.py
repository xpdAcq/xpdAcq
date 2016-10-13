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
from xpdacq.utils import import_sample
from bluesky.examples import motor, det, Reader

# print messages for debugging
#prun.msg_hook = print

class BeamtimeObjTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = 300000  # must be 300000  => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),
                              ('Terban ',' Max',2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        xlf = '300000_sample.xlsx'
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl.import_dir, xlf))

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir,'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir,'pe2_data'))


    def test_import_sample(self):
        # direct sample -> no ipython session, fail as expect
        self.assertRaises(AttributeError, lambda: import_sample())
        # explict import
        import_sample(300000, self.bt)
        # incorrect file name
        self.assertRaises(FileNotFoundError,
                          lambda: import_sample(12345, self.bt))
