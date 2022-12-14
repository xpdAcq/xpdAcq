"""Set up the objects ipython profile."""
import os
import typing as T
from pathlib import Path, PurePath

from bluesky.callbacks.zmq import Publisher
from databroker.v2 import Broker
from ophyd import Device

from xpdacq.beamtimeSetup import _start_beamtime, start_xpdacq
from xpdacq.calib2 import RunCalibration
from xpdacq.preprocessors import (CalibPreprocessor, DarkPreprocessor,
                                  ShutterConfig, ShutterPreprocessor)
from xpdacq.xpdacq import CustomizedRunEngine, xpdAcqError
from xpdacq.xpdacq_conf import (GlblYamlDict, _load_beamline_config,
                                _reload_glbl, _set_glbl, configure_device,
                                xpd_configuration)

Address = T.Union[T.Tuple[str, int], str]


def _rename_calib_file_suffix(glbl: dict) -> None:
    if "calib_config_name" not in glbl:
        return
    glbl["calib_config_name"] = PurePath(glbl["calib_config_name"]).with_suffix(".poni").name
    return


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


def _add_many_calib_preprocessors(
    xrun: CustomizedRunEngine,
    dets: T.List[Device],
    det_zs: T.List[T.Optional[Device]]
) -> None:
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


def _set_calib_preprocessor(cpp: CalibPreprocessor, glbl: GlblYamlDict, det_z: T.Optional[Device]) -> None:
    poni_file = Path(glbl["config_base"]).joinpath(glbl["calib_config_name"])
    if poni_file.is_file():
        calib_result = cpp.read(poni_file)
        if det_z is not None and hasattr(det_z, "get"):
            cpp.add_calib_result({det_z.name: det_z.get()}, calib_result)
        else:
            cpp.add_calib_result({}, calib_result)
    else:
        print(
            "WARNING: '{}' doesn't exist. "
            "Please do the calibration before you conduct measurement.".format(
                str(poni_file)
            )
        )
    return


class UserInterface:
    """The user interface of xpdAcq.

    It contains the necessary python objects that user will interact with in the ipython session.
    Be ware that initiation will change the home directory to the one specified in glbl.

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
    run_calibration: Callable
        A callable object to control the calibration preprocessors in the xrun.
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
        shutter_config: T.Optional[ShutterConfig] = None,
        glbl_yaml: str = None,
        blconfig_yaml: str = None,
        publish_to: Address = "localhost:5567",
        verbose: int = 1,
        test: bool = False
    ):
        """Create the python objects for the ipython session.

        Parameters
        ----------
        area_dets : T.List[Device]
            A list of the area detectors
        det_zs : T.List[T.Optional[Device]]
            A list of the motor that controls the z axis of the detectors, None if not exists
        shutter : Device
            A fast shutter
        temp_controller : Device
            A temperature controller
        filter_bank : Device
            A filter bank device
        ring_current : Device
            A ring current SynAxis
        db : Broker
            A databroker.
        shutter_config : T.Optional[ShutterConfig], optional
            The configuration for the shutter, by default, use the settings in the xpdacq configuration file
        glbl_yaml : str, optional
            The path to the glbl yaml file, by default None
        blconfig_yaml : str, optional
            The path to the beamline configuration file, by default None
        publish_to : _type_, optional
            The address to publish the data to, by default "localhost:5567"
        verbose : int, optional
            The verbose level when creating the objects, by default 1
        test : bool, optional
            Used for pytest, by default False

        Raises
        ------
        xpdAcqError
            _description_
        """
        if len(area_dets) == 0:
            raise xpdAcqError("There must be no less than one `area_dets`.")
        # add verbose
        self._verbose = verbose
        # configure devices
        self._print("INFO: Initializing the XPD data acquisition environment.")
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
        self._print("reload the global configuration.")
        from xpdacq.glbl import glbl
        _glbl = _reload_glbl(glbl_yaml)
        if _glbl:
            _set_glbl(glbl, _glbl)
        # load beamtime
        bt = start_xpdacq()
        if bt:
            self._print("Reload beamtime objects:\n{}\n".format(bt))
        elif test:
            bt = _start_beamtime("Billinge", 300000, wavelength=0.1675, test=True)
        else:
            self._print("No Beamtime object.")
        # instantiate xrun without beamtime, like bluesky setup
        self._print("Create xrun object.")
        xrun = CustomizedRunEngine(None)
        # add xrun into the xpd_configuration so that glbl can tune dark window
        xpd_configuration["xrun"] = xrun
        xrun.md["beamline_id"] = glbl["beamline_id"]
        xrun.md["group"] = glbl["group"]
        xrun.md["facility"] = glbl["facility"]
        if not blconfig_yaml:
            blconfig_yaml = glbl["blconfig_path"]
        xrun.md["beamline_config"] = _load_beamline_config(blconfig_yaml, test=test)
        # rename the suffix
        _rename_calib_file_suffix(glbl)
        # insert header to db, either simulated or real
        self._print("Subscribe database.")
        xrun.subscribe(db.v1.insert)
        if bt:
            xrun.beamtime = bt
        # add publisher
        self._print("Subscribe publisher, publishing to '{}'.".format(publish_to))
        pub = Publisher(publish_to, prefix=b'raw')
        xrun.subscribe(pub)
        # add dark preprocessors
        self._print("Subscribe preprocessors.")
        sc = ShutterConfig.from_xpdacq() if shutter_config is None else shutter_config
        _add_many_dark_preprocessors(xrun, area_dets, sc)
        _add_many_calib_preprocessors(xrun, area_dets, det_zs)
        _add_many_shutter_preprocessors(xrun, area_dets, sc)
        # add run calibration
        self._print("Create run_calibration.")
        run_calibration = RunCalibration(xrun, glbl)
        # set the first calibration preprocessor
        _set_calib_preprocessor(xrun.calib_preprocessors[0], glbl, det_zs[0])
        # register as attributes
        self._print("Register attributes.")
        self.glbl = glbl
        self.xpd_configuration = xpd_configuration
        self.bt = bt
        self.xrun = xrun
        self.run_calibration = run_calibration
        # Change directory
        if not test:
            home_dir = Path(glbl["home"])
            base_dir = Path(glbl["base"])
            if home_dir.is_dir():
                self._print("Change current directory to '{}'.".format(str(home_dir)))
                os.chdir(home_dir)
            elif base_dir.is_dir():
                self._print("Change current directory to '{}'.".format(str(base_dir)))
                os.chdir(base_dir)

    def _print(self, *args, **kwargs):
        if self._verbose > 0:
            print("INFO:", *args, **kwargs)
        return
