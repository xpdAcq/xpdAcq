from mock import MagicMock
from xpdacq.new_xpdAcq  import CustomizedRunEngine, ScanPlan, ct
from xpdacq import glbl
from bluesky.examples import motor, det, Reader

prun = CustomizedRunEngine({})
# print messages for debugging
prun.msg_hook = print


class SimulatedPE1C(Reader):
    "Subclass the bluesky plain detector examples ('Reader'); add attributes."
    def __init__(self, name, fields):
        self.images_per_set = MagicMock()
        self.number_of_sets = MagicMock()
        self.cam = MagicMock()
        self.frame_acq_time = MagicMock()
        super().__init__(name, fields)

        self.ready = True  # work around a hack in Reader


glbl.pe1c = SimulatedPE1C('pe1c', ['pe1c'])
glbl.shutter = motor  # this passes as a fake shutter
glbl.frame_acq_time = 0.1


def test_print_scanplan():
    sp1 = ScanPlan(ct, 1)  # using positional args
    sp2 = ScanPlan(ct, exposure=1)  # using kwargs is equivalent
    assert str(sp1) == str(sp2)


def test_run_scanplan():
    sp = ScanPlan(ct, 1)
    prun({}, sp)
