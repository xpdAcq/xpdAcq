import bluesky.plans as bp
import numpy as np
from bluesky import RunEngine
from bluesky_darkframes.sim import DiffractionDetector, Shutter
from databroker.v2 import temp
from xpdacq.preprocessors import DarkPreprocessor, ShutterConfig


def test_in_a_run():
    detector = DiffractionDetector(name="detector")
    shutter = Shutter(name="shutter", value="open")
    db = temp()
    RE = RunEngine()
    RE.subscribe(db.v1.insert)
    # test dark preprocessor
    dp = DarkPreprocessor(
        detector=detector, shutter_config=ShutterConfig(shutter, "open", "closed")
    )
    plan = dp(bp.count([detector]))
    RE(plan)
    del RE, plan, dp, shutter, detector
    # check the events
    light_data = db[-1].primary.read()
    dark_data = db[-1].dark.read()
    light_image = light_data["detector_image"].data[0]
    dark_image = dark_data["detector_image"].data[0]
    assert np.sum(light_image - dark_image) > 0.0
