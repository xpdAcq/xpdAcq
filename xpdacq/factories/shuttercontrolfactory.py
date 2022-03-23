import typing as T

import bluesky.plan_stubs as bps


class ShutterControlFactory:
    """The factory to produce plan stubs involving the control of the shutter.

    Each method will return a plan stub function which can be used in the bluesky plans.
    The plan stub is to open the shutter before the detector is triggered and close after
    it is read.
    """

    def __init__(
        self,
        *,
        open_shutter: T.Optional[T.Callable] = None,
        close_shutter: T.Optional[T.Callable] = None
    ) -> None:
        if open_shutter is None:
            from xpdacq.beamtime import open_shutter_stub
            open_shutter = open_shutter_stub
            del open_shutter_stub
        if close_shutter is None:
            from xpdacq.beamtime import close_shutter_stub
            close_shutter = close_shutter_stub
            del close_shutter_stub
        self._open_shutter = open_shutter
        self._close_shutter = close_shutter

    def get_take_reading(self):

        def take_reading(detectors, name="primary"):
            yield from self._open_shutter()
            result = (yield from bps.trigger_and_read(detectors))
            yield from self._close_shutter()
            return result

        return take_reading

    def get_per_shot(self):

        take_reading = self.get_take_reading()

        def per_shot(detectors):
            return (yield from bps.one_shot(detectors, take_reading=take_reading))

        return per_shot

    def get_per_step(self):

        take_reading = self.get_take_reading()

        def per_step(detectors, step, pos_cache):
            return (yield from bps.one_nd_step(detectors, step, pos_cache, take_reading=take_reading))

        return per_step
