from xpdacq.new_xpdacq.xpdacq import *
from xpdacq.new_xpdacq.beamtimeSetup import _end_beamtime, _start_beamtime
from xpdacq.new_xpdacq.beamtime import *
bt = _start_beamtime('alva', '1234', experimenters=[], wavelength=0.1828)
Experiment('temp_test', bt)
ScanPlan(bt.experiments[0], ct, 10)
Sample('test_sample', composition={})
bt.list()
