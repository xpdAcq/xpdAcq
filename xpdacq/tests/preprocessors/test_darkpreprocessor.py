from xpdacq.preprocessors.darkpreprocessor import DarkPreprocessor
from bluesky_darkframes.sim import Shutter, DiffractionDetector
import bluesky.plans as bp
from bluesky import RunEngine
from databroker import Broker
from ophyd.sim import NumpySeqHandler
import numpy as np


def test_in_a_run():
    detector = DiffractionDetector(name="detector")
    shutter = Shutter(name="shutter", value="open")
    dp = DarkPreprocessor(
        detector=detector,
        shutter=shutter,
        open_state="open",
        close_state="closed",
    )
    plan = dp(bp.count([detector]))
    db = Broker.named('temp')
    db.reg.register_handler('NPY_SEQ', NumpySeqHandler)
    RE = RunEngine()
    RE.subscribe(db.insert)
    RE(plan)
    del RE, plan, dp, shutter, detector
    # check the events
    dark_image = list(db[-1].data('detector_image'))[0]
    light_image = list(db[-1].data('detector_image', stream_name='dark'))[0]
    assert not np.allclose(dark_image, light_image)
