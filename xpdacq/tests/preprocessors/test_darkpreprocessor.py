import bluesky.plan_stubs as bps
import bluesky.plans as bp
import numpy as np
from bluesky import RunEngine
from bluesky_darkframes.sim import DiffractionDetector, Shutter
from databroker import Broker
from ophyd.sim import NumpySeqHandler
from xpdacq.preprocessors.darkpreprocessor import DarkPreprocessor


def test_in_a_run():
    detector = DiffractionDetector(name="detector")
    shutter = Shutter(name="shutter", value="open")
    db = Broker.named('temp')
    db.reg.register_handler('NPY_SEQ', NumpySeqHandler)
    RE = RunEngine()
    RE.subscribe(db.insert)

    def open_shutter():
        return (yield from bps.mv(shutter, "open"))

    def close_shutter():
        return (yield from bps.mv(shutter, "closed"))

    # test dark preprocessor
    dp = DarkPreprocessor(
        detector=detector,
        open_shutter=open_shutter,
        close_shutter=close_shutter
    )
    plan = dp(bp.count([detector]))
    RE(plan)
    del RE, plan, dp, shutter, detector
    # check the events
    dark_image = list(db[-1].data('detector_image'))[0]
    light_image = list(db[-1].data('detector_image', stream_name='dark'))[0]
    assert np.sum(light_image - dark_image) > 0.
