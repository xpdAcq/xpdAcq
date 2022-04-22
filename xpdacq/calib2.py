import typing as T
from pathlib import Path
import time

import bluesky.preprocessors as bpp
from ophyd import Device
import bluesky.plans as bp
from xpdacq.xpdacq import CustomizedRunEngine, xpdAcqException
from xpdacq.beamtime import configure_area_det
from xpdacq.xpdacq_conf import GlblYamlDict
from hashlib import sha256
from xpdacq.utils import ExceltoYaml

CalibMetaData = T.Dict[str, T.Any]
SampleMetaData = T.Dict[str, T.Any]
_INFO = """INFO: Please navigate to the pyFAI-calib2 window to finish the calibration.
Once the calbration file is saved or replaced, the session will be terminated.

Please read visit the website below to learn more about how to use the pyFAI-calib2.

https://pyfai.readthedocs.io/en/master/usage/cookbook/calib-gui/index.html#cookbook-calibration-gui
"""


class RunCalibration():
    """Run calibration.

    Collect image with metadata and send it to the analysis server.
    The analysis server will start a pyFAI-calib2 interactive session for user.
    Once user finishes the calibration and saves the file, the file will be read.
    The calibration preprocessor will be record the calibration result in its cache.

    Parameters
    ----------
    exposure : float, optional
        The in seconds for exposure of one image, by default 5.
    calibrant : str, optional
        The name of the calibration, like the calibrant name in the pyFAI-calib2 calibrant
        list, by default "Ni_calib"
    phase_info : str, optional
        The information of the phase, by default "Ni"
    detector : str, optional
        The detector name in the pyFAI-calib2 detector list, by default "'perkin-elmer"
    RE_instance : CustomizedRunEngine, optional
        The `xrun` object to use, by default None
    wait_for_cal : bool, optional
        Whether to wait for the file to be updated, by default True
    preprocessor_id : int, optional
        The index of the calibration preprocessor to set in the xrun.calib_preprocessors, by default 0
    """

    def __init__(self, xrun: CustomizedRunEngine, glbl: GlblYamlDict) -> None:
        if "config_base" not in glbl:
            raise xpdAcqException("Error: `glbl` doesn't have the key 'config_base'.")
        if "calib_config_name" not in glbl:
            raise xpdAcqException("Error: `glbl` doesn't have the key 'calib_config_name'.")
        if "frame_acq_time" not in glbl:
            raise xpdAcqException("Error: `glbl` doesn't have the key 'frame_acq_time'.")
        self._xrun = xrun
        self._glbl = glbl

    @staticmethod
    def _sample_name_phase_info_configuration(
        sample_name: str,
        phase_info: str
    ) -> SampleMetaData:
        sample_md = ExceltoYaml.parse_phase_info(phase_info)
        sample_md.update({"sample_name": sample_name})
        return sample_md

    def _get_calib_file(self) -> Path:
        return Path(self._glbl["config_base"]).joinpath(self._glbl["calib_config_name"])

    def _collect_metadata(
        self,
        sample_name: str,
        phase_info: str,
        detector_type: str
    ) -> CalibMetaData:
        md = self._sample_name_phase_info_configuration(sample_name, phase_info)
        md["pyfai_calib_kwargs"] = {
            "calibrant": sample_name,
            "detector": detector_type,
            "wavelength": self._xrun.beamtime.wavelength,
            "poni": str(self._get_calib_file())
        }
        return md

    @staticmethod
    def _collect_image(
        xrun: CustomizedRunEngine,
        glbl: GlblYamlDict,
        detector: Device,
        exposure: float,
        metadata: CalibMetaData
    ) -> T.Any:
        plan = bpp.pchain(
            configure_area_det(detector, exposure, glbl["frame_acq_time"]),
            bp.count([detector])
        )
        return xrun(metadata, plan)

    @staticmethod
    def _get_hash(filename: Path) -> str:
        if not filename.is_file():
            return ''
        with filename.open('r') as f:
            file_hash = sha256(f.read().encode("utf-8")).hexdigest()
        return file_hash

    def _wait_for_update(self, filename: Path, old_file_hash: str, wait: bool = True) -> None:
        if not wait:
            return
        while True:
            new_file_hash = self._get_hash(filename)
            if new_file_hash != old_file_hash:
                break
            time.sleep(1.)
        return

    def __call__(
        self,
        *,
        exposure: float = 5.,
        calibrant: str = "Ni",
        phase_info: str = "Ni",
        detector: str = "'perkin-elmer",
        RE_instance: CustomizedRunEngine = None,
        wait_for_cal: bool = True,
        preprocessor_id: int = 0
    ) -> None:
        # rename inputs
        xrun = self._xrun if RE_instance is None else RE_instance
        glbl = self._glbl
        del RE_instance
        detector_type = detector
        del detector
        sample_name = calibrant
        del calibrant
        # check
        n = len(xrun.calib_preprocessors)
        if n == 0:
            raise xpdAcqException("Error: there is no calibration preprocessors subscribed in the xrun.")
        if not (-1 < preprocessor_id < n):
            raise xpdAcqException(
                "Error: there is no calibration preprocessor with index '{}'.".format(preprocessor_id))
        cpp = xrun.calib_preprocessors[preprocessor_id]
        # hash file content before calibration
        calib_file = self._get_calib_file()
        old_file_hash = self._get_hash(calib_file)
        # collect metadata and data
        metadata = self._collect_metadata(sample_name, phase_info, detector_type)
        self._collect_image(xrun, glbl, cpp.detector, exposure, metadata)
        # wait for update
        print(_INFO)
        self._wait_for_update(calib_file, old_file_hash, wait_for_cal)
        # set the calibration result
        if calib_file.is_file():
            calib_result = cpp.read(calib_file)
            xrun({}, cpp.record(calib_result))
        return
