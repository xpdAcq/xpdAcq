#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
import time
from hashlib import sha256

import bluesky.preprocessors as bpp
from pyFAI.gui.cli_calibration import Calibration

from .beamtime import ScanPlan, ct
from .glbl import glbl
from .tools import _check_obj, xpdAcqException
from .utils import ExceltoYaml

_REQUIRED_OBJ_LIST = ["xrun"]


def _sample_name_phase_info_configuration(sample_name, phase_info, tag):
    """function to configure sample_name and phase_info"""
    if sample_name and phase_info:
        pass  # user defined, pass
    elif sample_name is None and phase_info is None:
        if tag == "calib":
            sample_name = "Ni_calib"
            phase_info = "Ni"
    else:
        raise xpdAcqException(
            "Ambiguous sample information. "
            "Only ``phase_info`` or ``sample_name``"
            "is supplied. Please provide both "
            "fields if you wish to specify full "
            "information, or leave both as None as"
            "default."
        )
    sample_md = ExceltoYaml.parse_phase_info(phase_info)
    sample_md.update({"sample_name": sample_name})

    return sample_md


def run_calibration(
        exposure=5,
        dark_sub_bool=True,
        calibrant=None,
        phase_info=None,
        detector=None,
        *,
        RE_instance=None,
        wait_for_cal=True,
        **kwargs
):
    """function to run entire calibration process.

    Entire process includes:

    1. collect calibration image,

    2. trigger pyFAI interactive calibration process,

    3. store calibration parameters as a yaml file

    calibration parameters will be saved under xpdUser/config_base/
    and this set of parameters will be injected as metadata to
    subsequent scans until you perform this process again

    Parameters
    ----------
    exposure : int, optional
        total exposure time in sec. default is 5s
    dark_sub_bool : bool, optional
        option of turn on/off dark subtraction on this calibration
        image. default is True.
    calibrant : str, optional
        calibrant being used, default is 'Ni'.
        input could be full file path to customized d-spacing file with
        ".D" extension or one of pre-defined calibrant names.
        List of pre-defined calibrant names is:
        ['NaCl', 'AgBh', 'quartz', 'Si_SRM640', 'Ni', 'Si_SRM640d',
        'Si_SRM640a', 'alpha_Al2O3', 'LaB6_SRM660b', 'TiO2', 'CrOx',
        'LaB6_SRM660c', 'CeO2', 'Si_SRM640c', 'CuO', 'Si_SRM640e',
        'PBBA', 'ZnO', 'Si', 'C14H30O', 'cristobaltite', 'LaB6_SRM660a',
        'Au', 'Cr2O3', 'Si_SRM640b', 'LaB6', 'Al', 'mock']
    phase_info : str, optional
        phase infomation of calibrant, which is required to data
        reduction process. This field will be parsed with the same logic
        as the one used in parsing spreadsheet information. For detailed
        information, please visit:
        http://xpdacq.github.io/usb_Running.html#phase-string
        If both ``calibrant`` and ``phase_info`` arguments are not provided,
        this field will be defaulted to ``Ni``.
    detector : str or pyFAI.detector.Detector instance, optional.
        detector used to collect data. default value is 'perkin-elmer'.
        other allowed values are in pyFAI documentation.
    RE_instance : bluesky.run_engine.RunEngine instance, optional
        instance of run engine. Default is xrun. Do not change under
        normal circumstances.
    wait_for_cal : bool
        If True wait for the new calibration to be produced before giving up
        xrun control, otherwise give up control at the end of the scan.
        Defaults to True
    kwargs:
        Additional keyword argument for calibration. please refer to
        pyFAI documentation for all options.

    Note
    ----
    Details about peak-picking gui from pyFAI documentaion

      http://pyfai.readthedocs.io/en/latest/usage/cookbook/calibrate.html#start-pyfai-calibration_md
    """
    # default information
    if detector is None:
        detector = "perkin_elmer"
    sample_md = _sample_name_phase_info_configuration(
        calibrant, phase_info, "calib"
    )
    if calibrant is None:
        calibrant = os.path.join(glbl["usrAnalysis_dir"], "Ni24.D")

    # collect & pull subtracted image
    if RE_instance is None:
        xrun_name = _REQUIRED_OBJ_LIST[0]
        RE_instance = _check_obj(xrun_name)  # will raise error if not exists

    calib_file = os.path.join(glbl["config_base"], glbl["calib_config_name"])
    calib_file_hash = '1'
    if os.path.exists(calib_file):
        with open(calib_file, 'r') as f:
            calib_file_hash = sha256(f.read().encode('utf-8')).hexdigest()

    _collect_img(
        exposure,
        dark_sub_bool,
        sample_md,
        "calib",
        RE_instance,
        detector=detector,
        calibrant=calibrant,
    )
    print(
        "INFO: Please navigate to the analysis terminal to complete "
        "the interactive calibration process.\nYou may find the "
        "the analysis terminal similar to data acquisition terminal"
        "(current terminal) except there is information about the "
        "analysis pipeline printed"
    )
    print(
        "INFO: For a quick guide on the interactive calibration "
        "process, please visit our web-doc at:\n"
        "https://xpdacq.github.io/xpdAcq/usb_Running.html#calib-manual\n"
    )
    if wait_for_cal:  # pragma: no cover
        print('Waiting for calibration to finish\n\n'
              'If calibration has failed please press Ctrl+C in this '
              'terminal and run ``run_calibration`` again!\n\n')
        while True:
            if os.path.exists(calib_file):
                with open(calib_file, 'r') as f:
                    new_calib_file_hash = sha256(f.read().encode('utf-8')).hexdigest()
            else:
                new_calib_file_hash = '1'
            if new_calib_file_hash != calib_file_hash:
                break
            else:
                time.sleep(1)
    """
    if not parallel:  # backup when pipeline fails
        # get wavelength from bt
        if wavelength is None:
            bt_fp = os.path.join(glbl["yaml_dir"], "bt_bt.yml")
            if not os.path.isfile(bt_fp):
                raise FileNotFoundError(
                    "Can't find your Beamtime yaml file.\n"
                    "Did you accidentally delete it? "
                    "Please contact beamline staff "
                    "ASAP"
                )
            bto = Beamtime.from_yaml(open(bt_fp))
            wavelength = float(bto.wavelength) * 10 ** (-10)
        # configure calibration instance
        c = Calibration(
            calibrant=calibrant, detector=detector, wavelength=wavelength
        )
        # pyFAI calibration
        calib_c, timestr = _calibration(img, c, fn_template, **kwargs)
        assert calib_c.calibrant.wavelength == wavelength
        # save param for xpdAcq
        yaml_name = glbl["calib_config_name"]
        calib_yml_fp = os.path.join(
            glbl["config_base"], glbl["calib_config_name"]
        )
        _save_calib_param(calib_c, timestr, calib_yml_fp)
    """


def _inject_calibration_tag(msg):
    if msg.command == "open_run":
        msg.kwargs["is_calibration"] = True
    return msg


def _collect_img(
        exposure,
        dark_sub_bool,
        sample_md,
        tag,
        RE_instance,
        *,
        calibrant=None,
        detector=None
):
    """helper function to collect image and return it"""
    # grab beamtime object linked to run_engine
    bto = RE_instance.beamtime
    plan = ScanPlan(bto, ct, exposure).factory()
    sample_md.update(bto)

    if tag == "calib":
        # instantiate Calibrant class
        calibrant_obj = Calibration(calibrant=calibrant).calibrant
        if calibrant_obj is None:
            raise xpdAcqException("Invalid calibrant")
        dSpacing = calibrant_obj.dSpacing
        if not dSpacing:
            raise xpdAcqException("empty dSpacing from calibrant")
        sample_md.update({"dSpacing": dSpacing, "detector": detector})
        plan = bpp.msg_mutator(plan, _inject_calibration_tag)

    # collect image
    RE_instance(sample_md, plan)
    """
    # last one must be light
    db = xpd_configuration["db"]
    light_header = db[uid[-1]]
    dark_uid = light_header["start"].get("sc_dk_field_uid")
    dark_header = db[dark_uid]
    dark_img = dark_header.data(glbl["image_field"])
    dark_img = np.asarray(next(dark_img)).squeeze()
    img = light_header.data(glbl["image_field"])
    img = np.asarray(next(img)).squeeze()

    if dark_sub_bool:
        img -= dark_img
    # FIXME: filename template from xpdAn
    fn_template = "from_calib_func_{}.poni".format(_timestampstr(time.time()))

    return img, fn_template
    """
