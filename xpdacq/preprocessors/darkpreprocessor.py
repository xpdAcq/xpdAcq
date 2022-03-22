import typing as T

import bluesky.plan_stubs as bps
from bluesky_darkframes import DarkFramePreprocessor, SnapshotDevice
from ophyd import Device
from ophyd.ophydobj import OphydObject
from ophyd.signal import Signal


class DarkPreprocessor(DarkFramePreprocessor):
    """A plan preprocessor that ensures each Run records a dark frame.

    Specifically this adds a new Event stream, named ‘dark’ by default. It inserts one Event with a reading that contains a ‘dark’ frame. The same reading may be used across multiple runs, depending on the rules for when a dark frame is taken.

    Parameters
    ----------
    shutter : OphydObject
        The fast shutter. It is usually a positionor.
    open_state : Any
        The position of the shutter when it is open.
    close_state : Any
        The position of the shutter when it is close.
    detector: Device
        The detector to take dark frame of.
    max_age: float
        Time after which a fresh dark frame should be acquired
    locked_signals: Iterable, optional
        Any changes to these signals invalidate the current dark frame and
        prompt us to take a new one. Typical examples would be exposure time or
        gain, anything that changes the expected dark frame.
    limit: integer or None, optional
        Number of dark frames to cache. If None, do not limit.
    stream_name: string, optional
        Event stream name for dark frames. Default is 'dark'.
    """

    def __init__(
        self,
        *,
        shutter: OphydObject,
        open_state: T.Any,
        close_state: T.Any,
        detector: Device,
        max_age: float = 0.,
        locked_signals: T.Optional[T.Iterable[Signal]] = None,
        limit: T.Optional[int] = None,
        stream_name='dark'
    ):

        def _dark_plan(_detector):
            yield from bps.unstage(_detector)
            yield from bps.stage(_detector)
            yield from bps.abs_set(shutter, open_state, wait=True)
            yield from bps.trigger(_detector, group='bluesky-darkframes-trigger')
            yield from bps.wait('bluesky-darkframes-trigger')
            yield from bps.abs_set(shutter, close_state)
            snapshot = SnapshotDevice(_detector)
            yield from bps.unstage(_detector)
            yield from bps.stage(_detector)
            return snapshot

        super().__init__(
            dark_plan=_dark_plan,
            detector=detector,
            max_age=max_age,
            locked_signals=locked_signals,
            limit=limit,
            stream_name=stream_name
        )
