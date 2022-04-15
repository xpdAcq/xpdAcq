import typing as T
from pathlib import Path

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import fabio
import numpy as np
from bluesky import Msg
from ophyd import Device, Signal

Plan = T.Generator[Msg, T.Any, T.Any]


class MaskPreprocessorError(Exception):

    pass


def _load_mask(mask_file: str) -> np.ndarray:
    path = Path(mask_file)
    if not path.is_file():
        raise MaskPreprocessorError("Mask file '{}' doesn't exist.".format(str(path)))
    if path.suffix in (".tiff", ".tif", ".edf"):
        return fabio.open(mask_file).data
    elif path.suffix == ".npy":
        return np.load(mask_file)
    elif path.suffix == ".txt":
        return np.loadtxt(mask_file)
    raise ValueError(
        "Unknown extension: {}. Only accept .tiff, .tif, .edf, .npy, .txt.".format(path.suffix)
    )


def _load_overlapping_masks(mask_files: T.List[str]) -> np.ndarray:
    masks = (_load_mask(f) for f in mask_files)
    return sum(masks)


class MaskPreprocessor:
    """Mutate the plan to push the mask data in the `mask` event stream right after the run open.

    Parameter
    ---------
    detector: Device
        The detector to use the mask for.
    stream_name: str
        The name of the event stream to push the mask, default "mask".
    """

    def __init__(self, detector: Device, stream_name: str = "mask") -> None:
        self._mask = Signal(name="{}_mask".format(detector.name), value=None)
        self._stream_name = stream_name

    def set_mask(self, mask: np.ndarray) -> None:
        if mask.ndim != 2:
            raise MaskPreprocessor("Mask dimsenions must be 2. This is {}.".format(mask.ndim))
        self._mask.put(mask)
        return

    def load_mask(self, mask_file: str) -> None:
        mask = _load_mask(mask_file)
        self.set_mask(mask)
        return

    def load_masks(self, mask_files: T.List[str]) -> None:
        mask = _load_overlapping_masks(mask_files)
        self.set_mask(mask)
        return

    def __call__(self, plan: Plan) -> Plan:
        if self._mask is None:
            return plan

        def _mutate(msg: Msg) -> T.Tuple[None, Plan]:
            if msg.command == "open_run":
                read_mask = bps.trigger_and_read(
                    [self._mask],
                    name=self._stream_name
                )
                return None, read_mask
            return None, None

        return bpp.plan_mutator(plan, _mutate)
