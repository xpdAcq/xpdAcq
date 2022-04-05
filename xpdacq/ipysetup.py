"""Set up the objects ipython profile."""
import typing as T

from databroker import Broker
from ophyd import Device

from xpdacq.preprocessors import (CalibPreprocessor, DarkPreprocessor,
                                  ShutterConfig, ShutterPreprocessor)

from .beamtimeSetup import start_xpdacq
from .xpdacq import CustomizedRunEngine, xpdAcqError
from .xpdacq_conf import (_load_beamline_config, _reload_glbl, _set_glbl,
                          configure_device)


def _get_locked_signals(det: Device) -> None:
    locked_signals = []
    if hasattr(det, "cam") and hasattr(det.cam, "acquire_time"):
        locked_signals.append(det.cam.acquire_time)
    if hasattr(det, "images_per_set"):
        locked_signals.append(det.images_per_set)
    return locked_signals


def _add_a_dark_preprocessor(xrun: CustomizedRunEngine, det: Device, sc: ShutterConfig) -> None:
    dpp = DarkPreprocessor(detector=det, max_age=6., locked_signals=_get_locked_signals(det), shutter_config=sc)
    xrun.dark_preprocessors.append(dpp)
    return


def _add_many_dark_preprocessors(xrun: CustomizedRunEngine, dets: T.List[Device], sc: ShutterConfig) -> None:
    for det in dets:
        _add_a_dark_preprocessor(xrun, det, sc)
    return


def _add_a_calib_preprocessor(xrun: CustomizedRunEngine, det: Device, det_z: T.Optional[Device]) -> None:
    locked_signals = [det_z] if det_z is not None else []
    cpp = CalibPreprocessor(detector=det, locked_signals=locked_signals)
    xrun.calib_preprocessors.append(cpp)
    return


def _add_many_calib_preprocessors(xrun: CustomizedRunEngine, dets: T.List[Device], det_zs: T.List[T.Optional[Device]]) -> None:
    for det, det_z in zip(dets, det_zs):
        _add_a_calib_preprocessor(xrun, det, det_z)
    return


def _add_a_shutter_preprocessor(xrun: CustomizedRunEngine, det: Device, sc: ShutterConfig) -> None:
    spp = ShutterPreprocessor(detector=det, shutter_config=sc)
    xrun.shutter_preprocessors.append(spp)
    return


def _add_many_shutter_preprocessors(xrun: CustomizedRunEngine, dets: T.List[Device], sc: ShutterConfig) -> None:
    for det in dets:
        _add_a_shutter_preprocessor(xrun, det, sc)
    return


class UserInterface:
    """The user interace of xpdAcq.

    It contiains the necessary python objects that user will interact with in the ipython session.

    Attributes
    ----------
    glbl: GlobalYamlDict
        The global configuration of the xpdAcq.
    xpd_configuration: Dict[str, Device]
        The mapping from the group name to one or multiple ophyd devices.
    bt: Beamtime
        The object containing the information about the beamtime.
    xrun: CustomizedRunEngine
        The xpdacq wrapper of the bluesky run engine.
    """

    def __init__(
        self,
        *,
        area_dets: T.List[Device],
        det_zs: T.List[T.Optional[Device]],
        shutter: Device,
        temp_controller: Device,
        filter_bank: Device,
        ring_current: Device,
        db: Broker,
        glbl_yaml: str = None,
        blconfig_yaml: str = None,
        test: bool = False
    ):
        if len(area_dets) == 0:
            raise xpdAcqError("There must be no less than one `area_dets`.")
        # configure devices
        configure_device(
            area_det=area_dets[0],
            shutter=shutter,
            temp_controller=temp_controller,
            filter_bank=filter_bank,
            ring_current=ring_current,
            db=db,
            other_dets=area_dets[1:]
        )
        # reload glbl
        from xpdacq.glbl import glbl
        _glbl = _reload_glbl(glbl_yaml)
        if _glbl:
            _set_glbl(glbl, _glbl)
        # load beamtime
        bt = start_xpdacq()
        if bt:
            print("INFO: Reload beamtime objects:\n{}\n".format(bt))
        else:
            print("INFO: No Beamtime object.")
        # instantiate xrun without beamtime, like bluesky setup
        xrun = CustomizedRunEngine(None)
        xrun.md["beamline_id"] = glbl["beamline_id"]
        xrun.md["group"] = glbl["group"]
        xrun.md["facility"] = glbl["facility"]
        if not blconfig_yaml:
            blconfig_yaml = glbl["blconfig_path"]
        xrun.md["beamline_config"] = _load_beamline_config(blconfig_yaml, test=test)
        # insert header to db, either simulated or real
        xrun.subscribe(db.v1.insert)
        if bt:
            xrun.beamtime = bt
        # add dark preprocessors
        sc = ShutterConfig.from_xpdacq()
        _add_many_dark_preprocessors(xrun, area_dets, sc)
        _add_many_calib_preprocessors(xrun, area_dets, det_zs)
        _add_many_shutter_preprocessors(xrun, area_dets, sc)
        # register as attributes
        from xpdacq.xpdacq_conf import xpd_configuration
        self.glbl = glbl
        self.xpd_configuration = xpd_configuration
        self.bt = bt
        self.xrun = xrun
