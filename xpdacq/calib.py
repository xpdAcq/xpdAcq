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
import uuid
import time
import yaml
import logging
import numpy as np
from IPython import get_ipython

import bluesky.plans as bp

from .glbl import glbl
from .xpdacq_conf import xpd_configuration
from .beamtime import Beamtime, ScanPlan, Sample, ct
from .tools import _timestampstr, _check_obj, xpdAcqException
from .utils import ExceltoYaml

from xpdan.tools import mask_img, compress_mask
from xpdan.calib import (_save_calib_param, _calibration)

from pyFAI.gui.utils import update_fig
from pyFAI.calibration import Calibration, PeakPicker, Calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

from pkg_resources import resource_filename as rs_fn

_REQUIRED_OBJ_LIST = ['xrun']

def run_calibration(exposure=5, dark_sub_bool=True,
                    calibrant=None, phase_info=None,
                    wavelength=None, detector=None,
                    *, RE_instance=None, parallel=True, **kwargs):
    """function to run entire calibration process.

    Entire process includes:
    1) collect calibration image,
    2) trigger pyFAI interactive calibration process,
    3) store calibration parameters as a yaml file

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
    wavelength : float, optional
        x-ray wavelength in angstrom. default to value stored in
        existing Beamtime object
    detector : str or pyFAI.detector.Detector instance, optional.
        detector used to collect data. default value is 'perkin-elmer'.
        other allowed values are in pyFAI documentation.
    RE_instance : bluesky.run_engine.RunEngine instance, optional
        instance of run engine. Default is xrun. Do not change under
        normal circumstances.
    parallel : bool, optional
        Tag for whether run the calibration step in a separte
        process. Running in parallel in principle yields better resource
        allocation. Default is ``True``, only change to ``False`` if
        error is raised.
    kwargs:
        Additional keyword argument for calibration. please refer to
        pyFAI documentation for all options.

    Reference
    ---------
    pyFAI documentation:
    http://pyfai.readthedocs.io/en/latest/
    """
    # get necessary info
    if detector is None:
        detector = 'perkin_elmer'
    if calibrant is None:
        calibrant = os.path.join(glbl['usrAnalysis_dir'], 'Ni24.D')
        if phase_info is None:
            phase_info = 'Ni'
        else:
            raise xpdAcqException("Ambiguous sample information. "
                                  "``phase_info`` is specified "
                                  "but ``calibrant`` is not supplied. "
                                  "Please provide both fields if you wish "
                                  "to specify information")
    else:
        # user specify calibrant but not phase_info
        raise xpdAcqException("Ambiguous sample information. "
                              "``calibrant`` is specified "
                              "but ``phase_info`` is not supplied. "
                              "Please provide both fields if you wish "
                              "to specify information")

    # collect & pull subtracted image
    if RE_instance is None:
        xrun_name = _REQUIRED_OBJ_LIST[0]
        xrun = _check_obj(xrun_name)  # will raise error if not exists
    img, fn_template = _collect_calib_img(exposure, dark_sub_bool,
                                          calibrant, phase_info,
                                          detector, xrun)

    if not parallel:  # backup when pipeline fails
        # get wavelength from bt
        if wavelength is None:
            bt_fp = os.path.join(glbl['yaml_dir'], 'bt_bt.yml')
            if not os.path.isfile(bt_fp):
                raise FileNotFoundError("Can't find your Beamtime yaml file.\n"
                                        "Did you accidentally delete it? "
                                        "Please contact beamline staff "
                                        "ASAP")
            bto = Beamtime.from_yaml(open(bt_fp))
            wavelength = float(bto.wavelength)*10**(-10)
        # configure calibration instance
        assert os.path.isfile(calibrant)
        c = Calibration(calibrant=calibrant,
                        detector=detector,
                        wavelength=wavelength)
        # pyFAI calibration
        calib_c, timestr = _calibration(img, c, fn_template,
                                        **kwargs)
        assert calib_c.calibrant.wavelength == wavelength
        # save param for xpdAcq
        yaml_name = glbl['calib_config_name']
        calib_yml_fp = os.path.join(glbl['config_base'],
                                    glbl['calib_config_name'])
        _save_calib_param(calib_c, timestr, calib_yml_fp)


def _collect_calib_img(exposure, dark_sub_bool, calibrant,
                       phase_info, detector, RE_instance):
    """helper function to collect calibration image and return it"""
    # get calibrant name by split path and ext -> works for str too
    stem, fn = os.path.split(calibrant)
    calibrant_name, ext = os.path.splitext(fn)
    # instantiate Calibrant class
    calibrant_obj = Calibrant(calibrant)
    # add _calib to avoid overwrite current sample objects
    # Note: in the future, this info should be draw from sample_db
    sample_md = ExceltoYaml.parse_phase_info(phase_info)
    sample_md.update({'sample_name': calibrant_name+'_calib',
                      'dSpacing': calibrant_obj.dSpacing,
                      'detector': detector})
    bto = RE_instance.beamtime  # grab beamtime object linked to run_engine
    sample = Sample(bto, sample_md)
    # annoying md detais -> since calib_md inject is looking for
    # open_run kwargs
    def _inject_calibration_tag(msg):
        if msg.command == 'open_run':
            msg.kwargs['is_calibration'] = True
        return msg
    plan = ScanPlan(bto, ct, exposure).factory()
    plan = bp.msg_mutator(plan, _inject_calibration_tag)
    uid = RE_instance(sample, plan)
    light_header = xpd_configuration['db'][uid[-1]]  # last one must be light
    dark_uid = light_header.start.get('sc_dk_field_uid')
    dark_header = xpd_configuration['db'][dark_uid]
    db = xpd_configuration['db']

    dark_img = dark_header.data(glbl['det_image_field'])
    dark_img = np.asarray(next(dark_img)).squeeze()

    img = light_header.data(glbl['det_image_field'])
    img = np.asarray(next(img)).squeeze()

    if dark_sub_bool:
        img -= dark_img
    # FIXME: filename template from xpdAn
    fn_template = None

    return img, fn_template


def run_mask_builder(exposure=300, mask_sample_name=None,
                     phase_info=None, dark_sub_bool=True,
                     polarization_factor=0.99,
                     calib_dict=None, mask_dict=None,
                     save_name=None, *, RE_instance=None):
    """function to build a mask based on image collected.

    this function will execute a count scan and generate a mask based on
    image collected from this scan.

    Parameters
    ----------
    exposure : float, optional
        exposure time of this scan. default is 300s.
    mask_sample_name : str, optional
        name of sample that new mask is going to be generated from.
        default is 'kapton'
    phase_info : str, optional
        phase information for the sample that new mask is going to be
        generated from. default is 'C12H12N2O'
    dark_sub_bool : bool, optional
        turn on/off of dark subtraction. default is True.
    polarization_factor: float, optional.
        polarization correction factor, ranged from -1(vertical) to +1
        (horizontal). default is 0.99. set to None for no correction.
    calib_dict : dict, optional
        dictionary with parameters for geometry correction
        software. default is read out from glbl attribute (parameters
        from the most recent calibration)
    mask_dict : dict, optional
        dictionary for arguments in masking function. for more details,
        please check docstring from ``xpdan.tools.mask_img``
    save_name : str, optional
        full path for this mask going to be saved. if it is None,
        default name 'xpdacq_mask.npy' will be saved inside
        xpdUser/config_base/
    RE_instance : bluesky.run_engine.RunEngine instance, optional
        instance of run engine. Default is xrun. Do not change under
        normal circumstances.

    Note
    ----
    current software dealing with geometry correction is ``pyFAI``

    See also
    --------
    xpdan.tools.mask_img
    """

    _check_obj(_REQUIRED_OBJ_LIST)
    ips = get_ipython()
    bto = ips.ns_table['user_global']['bt']
    xrun = ips.ns_table['user_global']['xrun']

    # default behavior
    if calib_dict is None:
        calib_dict = glbl.get('calib_config_dict', None)
        if calib_dict is None:
            print("INFO: there is no glbl calibration dictionary linked\n"
                  "Please do ``run_calibration()`` or provide your own"
                  "calibration parameter set")
            return
    # sample infomation
    if mask_sample_name is None and phase_info is None:
        mask_sample_name = 'kapton'
        phase_info = 'C12H12N2O'
    elif mask_sample_name and phase_info:
        pass
    else:
        raise xpdAcqException("Ambiguous sample information. "
                              "Either one of fields in the "
                              "Please provide both fields if you wish "
                              "to specify information")
    # grab RE instance
    if RE_instance is None:
        xrun_name = _REQUIRED_OBJ_LIST[0]
        xrun = _check_obj(xrun_name)  # will raise error if not exists

    img, fn_template = _collect_calib_img(exposure, dark_sub_bool,
                                          calibrant, phase_info,
                                          detector, xrun)
    if mask_dict is None:
        mask_dict = glbl['mask_dict']
    print("INFO: use mask options: {}".format(mask_dict))


    # setting up geometry parameters
    ai = AzimuthalIntegrator()
    ai.setPyFAI(**calib_dict)

    # scan
    mask_builder_dict = {'sample_name': sample_name,
                         'sample_composition': {sample_name: 1},
                         'is_build_mask': True}
    sample = Sample(bto, mask_builder_dict)
    xrun_uid = xrun(sample, ScanPlan(bto, ct, exposure))
    light_header = xpd_configuration['db'][-1]
    if dark_sub_bool:
        dark_uid = light_header.start['sc_dk_field_uid']
        dark_header = xpd_configuration['db'][dark_uid]

        dark_img = np.asarray(xpd_configuration['db'].get_images(
            dark_header, glbl['det_image_field'])).squeeze()

    for ev in xpd_configuration['db'].get_events(light_header, fill=True):
        img = ev['data'][glbl['det_image_field']]
        if dark_sub_bool:
            img -= dark_img

    img /= ai.polarization(img.shape, polarization_factor)
    mask = mask_img(img, ai, **mask_dict)

    if save_name is None:
        save_name = glbl['mask_path']
    # still save the most recent mask, as we are in file-based
    np.save(save_name, mask)

    return
