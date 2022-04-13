import collections
import itertools
import os
import tempfile
import threading
import time
import typing as T

import bluesky.plan_stubs as bps
import numpy as np
from bluesky import RunEngine
from bluesky.utils import short_uid
from bluesky_darkframes.sim import Shutter
from databroker import Broker
from ophyd import Component, Device, DeviceStatus, Kind, Signal, Staged
from ophyd.sim import new_uid
from pkg_resources import resource_filename
from tifffile import TiffFile

dark_frame_file = resource_filename("xpdacq", "data/Ni_dark_frame.tiff")
light_frame_file = resource_filename("xpdacq", "data/Ni_light_frame.tiff")
with TiffFile(dark_frame_file) as tf:
    dark_frame = tf.asarray()
with TiffFile(light_frame_file) as tf:
    light_frame = tf.asarray()
diffraction_pattern = light_frame
shutter_state = {'state': 'open'}


class Shutter(Signal):

    def put(self, value):
        shutter_state['state'] = value
        super().put(value)


def generate_image(dark=False, num=1):
    # TODO Add noise, zingers, and other nondeterministic things.
    output = dark_frame
    if not dark:
        output += diffraction_pattern
    return np.stack([output] * num)


class TimerStatus(DeviceStatus):
    """Simulate the time it takes for a detector to acquire an image."""

    def __init__(self, device, delay):
        super().__init__(device)
        self.delay = delay  # for introspection purposes
        threading.Timer(delay, self._finished).start()


class Camera(Device):

    acquire_time = Component(Signal, name="acquire_time", kind=Kind.config, value=0.1)


class PerkinElmerDetector(Device):

    cam = Component(Camera, name="cam")
    images_per_set = Component(Signal, name="images_per_set", kind=Kind.config, value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resource_uid = None
        self._datum_counter = None
        self._asset_docs_cache = collections.deque()
        self.save_path = tempfile.mkdtemp()

        self._path_stem = None
        self._stashed_image_reading = None
        self._stashed_image_data_key = None

    def stage(self):
        file_stem = short_uid()
        self._datum_counter = itertools.count()
        self._path_stem = os.path.join(self.save_path, file_stem)

        self._resource_uid = new_uid()
        resource = {'spec': 'NPY_SEQ',
                    'root': self.save_path,
                    'resource_path': file_stem,
                    'resource_kwargs': {},
                    'uid': self._resource_uid,
                    'path_semantics': {'posix': 'posix', 'nt': 'windows'}[os.name]}
        self._asset_docs_cache.append(('resource', resource))
        return super().stage()

    def trigger(self):
        if not self._staged == Staged.yes:
            raise RuntimeError("Device must be staged before it is triggered.")
        image = generate_image(
            dark=(shutter_state['state'] == 'closed'),
            num=self.images_per_set.get()
        )
        # Save the actual reading['value'] to disk. For a real detector,
        # this part would be done by the detector IOC, not by ophyd.
        data_counter = next(self._datum_counter)
        np.save(f'{self._path_stem}_{data_counter}.npy', image,
                allow_pickle=False)
        # Generate a stash and Datum document.
        datum_id = '{}/{}'.format(self._resource_uid, data_counter)
        datum = {'resource': self._resource_uid,
                 'datum_kwargs': dict(index=data_counter),
                 'datum_id': datum_id}
        self._asset_docs_cache.append(('datum', datum))
        self._stashed_image_reading = {'value': datum_id,
                                       'timestamp': time.time()}
        self._stashed_image_data_key = {'source': 'SIM:image',
                                        'shape': image.shape,
                                        'dtype': 'array',
                                        'external': 'FILESTORE'}
        delay = self.cam.acquire_time.get() * self.images_per_set.get()
        return TimerStatus(self, delay)

    def read(self):
        ret = super().read()
        ret[f'{self.name}_image'] = self._stashed_image_reading
        return ret

    def describe(self):
        ret = super().describe()
        ret[f'{self.name}_image'] = self._stashed_image_data_key
        return ret

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item

    def unstage(self):
        self._resource_uid = None
        self._datum_counter = None
        self._asset_docs_cache.clear()
        self._path_stem = None
        return super().unstage()


class Eurotherm(Signal):

    pass


class Stage(Device):

    x = Component(Signal, value=0., kind=Kind.hinted)
    y = Component(Signal, value=0., kind=Kind.hinted)
    z = Component(Signal, value=0., kind=Kind.hinted)


class FilterBank(Device):

    flt1 = Component(Signal, value="In")
    flt2 = Component(Signal, value="In")
    flt3 = Component(Signal, value="In")
    flt4 = Component(Signal, value="In")


class RingCurrent(Signal):

    pass


class WorkSpace:

    def __init__(self) -> None:

        self.RE: RunEngine = RunEngine()
        self.db: Broker = Broker.named("temp")
        self.RE.subscribe(self.db.insert)
        self.det: PerkinElmerDetector = PerkinElmerDetector(name="pe1")
        self.eurotherm: Eurotherm = Eurotherm(name="temperature")
        self.shutter: Shutter = Shutter(name="shutter")


def get_open_shutter(shutter: Shutter) -> T.Callable:

    def open_shutter():
        return (yield from bps.mv(shutter, "open"))

    return open_shutter


def get_close_shutter(shutter: Shutter) -> T.Callable:

    def close_shutter():
        return (yield from bps.mv(shutter, "closed"))

    return close_shutter
