import bluesky.plan_stubs as bps
from bluesky.simulators import summarize_plan
from ophyd.sim import hw

import xpdacq.plan_stubs as xps


def test_mv_and_trigger_and_read():
    devices = hw()
    plan = xps.mv_and_trigger_and_read([devices.det1], "primary", devices.motor1, 1,
                                       open_shutter=lambda: bps.mv(devices.motor2, 1),
                                       close_shutter=lambda: bps.mv(devices.motor2, 0))
    summarize_plan(plan)
