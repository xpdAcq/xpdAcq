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

from .glbl import glbl
from .xpdacq_conf import xpd_configuration
from .beamtime import Beamtime, ScanPlan, Sample, ct
from .tools import _timestampstr, _check_obj

from xpdan.tools import mask_img, compress_mask
from xpdan.calib import (_save_calib_param, _calibration,
                         _configure_calib_instance)

from pyFAI.gui.utils import update_fig
from pyFAI.calibration import Calibration, PeakPicker, Calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

from pkg_resources import resource_filename as rs_fn

_REQUIRED_OBJ_LIST = ['xrun']

def run_calibration(exposure=5, dark_sub_bool=True,
                    calibrant=None, wavelength=None,
                    detector=None, *, RE_instance=None,
                    detector_calibration_server_uid=None,
                    parallel=True, **kwargs):
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
    wavelength : float, optional
        x-ray wavelength in angstrom. default to value stored in
        existing Beamtime object
    detector : str or pyFAI.detector.Detector instance, optional.
        detector used to collect data. default value is 'perkin-elmer'.
        other allowed values are in pyFAI documentation.
    RE_instance : bluesky.run_engine.RunEngine instance, optional
        instance of run engine. Default is xrun. Do not change under
        normal circumstances.
    detector_calibration_server_uid : str, optional
        uid used to reference all required information for this
        calibration run. Subsequent datasets which reference the same
        experimental geometry as this calibration run are ``clients``.
        ``server`` and ``clients`` are linked by having the same
        value for client uid. For more details and motivation behind,
        please see: https://github.com/xpdAcq/xpdSchema
        By default a new uid is generated. Override default when
        you want to associate this new calibration with an existing
        detector_calibration_server_uid in previously collected run headers.
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
    # update calibration server uid in glbl
    if detector_calibration_server_uid is None:
        detector_calibration_server_uid = str(uuid.uuid4())
    glbl['detector_calibration_server_uid'] = detector_calibration_server_uid

    # get necessary info
    if detector is None:
        detector = 'perkin_elmer'
    if calibrant is None:
        calibrant = os.path.join(glbl['usrAnalysis_dir'], 'Ni24.D')

    # collect & pull subtracted image
    if RE_instance is None:
        xrun_name = _REQUIRED_OBJ_LIST[0]
        xrun = _check_obj(xrun_name)  # will raise error if not exists
    img = _collect_calib_img(exposure, dark_sub_bool, calibrant,
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
            wavelength = bto.wavelength
        # configure calibration instance
        c, dSpacing_list = _configure_calib_instance(calibrant,
                                                     detector,
                                                     wavelength)
        # pyFAI calibration
        calib_c, timestr = _calibration(img, c, glbl['config_base'],
                                        **kwargs)
        # save param for xpdAcq
        yaml_name = glbl['calib_config_name']
        calib_yml_fp = os.path.join(glbl['config_base'],
                                    glbl['calib_config_name'])
        _save_calib_param(calib_c, timestr, calib_yml_fp)


def _collect_calib_img(exposure, dark_sub_bool, calibrant,
                       detector, RE_instance):
    """helper function to collect calibration image and return it"""
    # get calibrant name by split path and ext -> works for str too
    stem, fn = os.path.split(calibrant)
    calibrant_name, ext = os.path.splitext(fn)
    # instantiate Calibrant class
    calibrant_obj = Calibrant(calibrant)
    # add _calib to avoid overwrite
    calibration_dict = {'sample_name': calibrant_name+'_calib',
                        'sample_composition': {calibrant_name: 1},
                        'is_calibration': True,
                        'dSpacing': calibrant_obj.dSpacing,
                        'detector': detector}
    bto = RE_instance.beamtime  # grab beamtime object linked to run_engine
    sample = Sample(bto, calibration_dict)
    uid = RE_instance(sample, ScanPlan(bto, ct, exposure))
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

    return img


def run_mask_builder(exposure=300, dark_sub_bool=True,
                     polarization_factor=0.99,
                     sample_name=None, calib_dict=None,
                     mask_dict=None, save_name=None,
                     mask_server_uid=None):
    """ function to generate mask

    this function will execute a count scan and generate a mask based on
    image collected from this scan.

    Parameters
    ----------
    exposure : float, optional
        exposure time of this scan. default is 300s.
    dark_sub_bool : bool, optional
        turn on/off of dark subtraction. default is True.
    polarization_factor: float, optional.
        polarization correction factor, ranged from -1(vertical) to +1
        (horizontal). default is 0.99. set to None for no correction.
    sample_name : str, optional
        name of sample that new mask is going to be generated from.
        default is 'mask_target'
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
    mask_server_uid : str, optional
        uid used to reference all required information for bulding a
        mask. Subsequent datasets that will use this mask are
        ``clients`` that hold a reference to the ``server`` with the
        correct experimental geometry and images by having the same
        value for client uid. For more details and motivation behind,
        please see: https://github.com/xpdAcq/xpdSchema.
        By default a new uid is generated. Override default when
        you want to associate this new mask with an existing
        mask-server-uid in previously collected run headers.
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

    if mask_server_uid is None:
        mask_server_uid = str(uuid.uuid4())
    glbl['mask_server_uid'] = mask_server_uid

    if sample_name is None:
        sample_name = 'mask_target'

    if mask_dict is None:
        mask_dict = glbl['mask_dict']
    print("INFO: use mask options: {}".format(mask_dict))


    # setting up geometry parameters
    ai = AzimuthalIntegrator()
    ai.setPyFAI(**calib_dict)

    # scan
    mask_builder_dict = {'sample_name': sample_name,
                         'sample_composition': {sample_name: 1},
                         'is_mask': True}
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
