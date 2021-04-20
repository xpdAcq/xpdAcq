"""Wrappers for the bluesky.plan_stubs"""
import typing

import bluesky.plan_stubs as bps
import ophyd


def mv_and_trigger_and_read(devices: typing.Iterable[ophyd.Device], name: str, *args,
                            open_shutter: typing.Callable, close_shutter: typing.Callable) -> typing.Generator:
    """Trigger and read multiple devices after moving one motor.

    Parameters
    ----------
    devices :
        The devices for trigger and read.

    name :
        The name of the stream.

    *args :
        A sequence of `motor, position`.

    open_shutter :
        The function to opne the shutter. `open_shutter()` is a generator of message to open the shutter.

    close_shutter :
        The open and close value for the shutter. `close_shutter()` is a generator of message to close the shutter.

    Returns
    -------
    Msg :
        The message.

    Examples
    --------
    If we would like to move the motor `det_Z` to 1000, collect image from detector `det` for a stream `XRD`.

    >>> plan = mv_and_trigger_and_read([det], "XRD", det_Z, 1000, open_shutter=open_shutter, close_shutter=close_shutter)
    """
    if args:
        yield from bps.mv(*args)
    yield from open_shutter()
    yield from bps.trigger_and_read(devices, name=name)
    yield from close_shutter()
