"""Dark frame plans."""
import bluesky.plan_stubs as bps
import bluesky_darkframes
import typing
from bluesky_darkframes import DarkFramePreprocessor

from ophyd import Device


def basic_dark_plan(
    detector: Device,
    shutter: Device,
    open_state: typing.Hashable,
    close_state: typing.Hashable
):
    """A basic dark frame plan."""
    # Restage to ensure that dark frames goes into a separate file.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)
    print("INFO: close the shutter ...")
    yield from bps.mv(shutter, close_state)
    # The `group` parameter passed to trigger MUST start with
    # bluesky-darkframes-trigger.
    print("INFO: take a dark frame ...")
    yield from bps.trigger(detector, group='bluesky-darkframes-trigger')
    yield from bps.wait('bluesky-darkframes-trigger')
    snapshot = bluesky_darkframes.SnapshotDevice(detector)
    print("INFO: open the shutter ...")
    yield from bps.mv(shutter, open_state)
    # Restage.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)
    return snapshot
