import pytest
import bluesky.plan_stubs as bps
from bluesky.plans import count
import bluesky_darkframes
from bluesky import RunEngine
import databroker
from ophyd.sim import NumpySeqHandler
from xpdsim import xpd_pe1c
from xpdacq.xpdacq_conf import xpd_configuration
from xpdacq.xpdacq import xpdacq_mutator

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


@pytest.fixture
def RE(fresh_xrun):
    RE = RunEngine2()
    db = databroker.v2.temp()
    RE.subscribe(db.v1.insert)
    dark_frame_preprocessor = bluesky_darkframes.DarkFramePreprocessor(
        dark_plan=dark_plan, detector=xpd_configuration["area_det"], max_age=0,
        locked_signals=[xpd_configuration["area_det"].cam.acquire_time, xpd_configuration["area_det"].images_per_set], limit=1)
    RE.preprocessors.append(dark_frame_preprocessor)
    return RE


class RunEngine2(RunEngine):
    def __int__(self, *args, **kwargs):
        super().__int__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


def test_temp(RE, bt):
    plan = xpdacq_mutator(
        beamtime=bt,
        sample=0,
        plan=0,
        robot=False,
        shutter_control=(xpd_configuration["shutter"], 0),
        auto_load_calib=True,
        verbose=1
    )
    RE(plan)
    return
