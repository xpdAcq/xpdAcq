import bluesky.plan_stubs as bps
from bluesky.plans import count
import bluesky_darkframes
from bluesky import RunEngine
import databroker
from ophyd.sim import NumpySeqHandler
from xpdsim import xpd_pe1c

# This is some simulated hardware for demo purposes.
from bluesky_darkframes.sim import Shutter, DiffractionDetector
det = DiffractionDetector(name='det')
shutter = Shutter(name='shutter', value='open')


def dark_plan(detector):
    # Restage to ensure that dark frames goes into a separate file.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)
    yield from bps.mv(shutter, 'closed')
    # The `group` parameter passed to trigger MUST start with
    # bluesky-darkframes-trigger.
    yield from bps.trigger(detector, group='bluesky-darkframes-trigger')
    yield from bps.wait('bluesky-darkframes-trigger')
    snapshot = bluesky_darkframes.SnapshotDevice(detector)
    yield from bps.mv(shutter, 'open')
    # Restage.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)
    return snapshot


def test_temp():
    db = databroker.v2.temp()
    RE = RunEngine()
    RE.subscribe(db.v1.insert)
    dark_frame_preprocessor = bluesky_darkframes.DarkFramePreprocessor(
        dark_plan=dark_plan, detector=xpd_pe1c, max_age=0,
        locked_signals=[xpd_pe1c.cam.acquire_time, xpd_pe1c.images_per_set], limit=1)
    RE.preprocessors.append(dark_frame_preprocessor)
    RE(count([det]))
    return
