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
import datetime
import numpy as np
from IPython import get_ipython

from .glbl import glbl
from .xpdacq_conf import xpd_configuration
from .beamtime import Beamtime, ScanPlan, Sample, ct
from .xpdacq import CustomizedRunEngine
from xpdan.tools import mask_img, compress_mask

from pyFAI.gui.utils import update_fig
from pyFAI.calibration import Calibration, PeakPicker
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

from pkg_resources import resource_filename as rs_fn

_REQUIRED_OBJ_LIST = ['xrun']


def show_calib():
    param = glbl.get('calib_config_dict', None)
    if not param:
        print("INFO: no calibration has been run yet")
    else:
        return param

def _check_obj(required_obj_list):
    """function to check if object(s) exist

    Parameter
    ---------
    required_obj_list : list
        a list of strings refering to object names

    """
    ips = get_ipython()
    for obj_str in required_obj_list:
        if not ips.ns_table['user_global'].get(obj_str, None):
            raise NameError("Required object {} doesn't exist in"
                            "namespace".format(obj_str))
    return


def _timestampstr(timestamp):
    """convert timestamp to strftime formate"""
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        '%Y%m%d-%H%M')
    return timestring


def run_calibration(exposure=5, dark_sub_bool=True,
                    calibrant=None, wavelength=None,
                    detector=None, *, RE_instance=None,
                    detector_calibration_server_uid=None, **kwargs):
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
    kwargs:
        Additional keyword argument for calibration. please refer to
        pyFAI documentation for all options.

    Reference
    ---------
    pyFAI documentation:
    http://pyfai.readthedocs.io/en/latest/
    """
    # configure calibration instance
    c = _configure_calib_instance(calibrant, detector, wavelength)

    # collect & pull subtracted image
    if detector_calibration_server_uid is None:
        detector_calibration_server_uid = str(uuid.uuid4())
    if RE_instance is None:
        _check_obj(_REQUIRED_OBJ_LIST)
        ips = get_ipython()
        xrun = ips.ns_table['user_global']['xrun']
    img = _collect_calib_img(exposure, dark_sub_bool,
                             c, xrun, detector_calibration_server_uid)

    # pyFAI calibration
    calib_c, timestr = _calibration(img, c, **kwargs)

    # save param for xpdAcq
    _save_and_attach_calib_param(calib_c, timestr,
                                 detector_calibration_server_uid)


def _configure_calib_instance(calibrant, detector, wavelength):
    """function to configure calibration instance"""
    if wavelength is None:
        bt_fp = os.path.join(glbl['yaml_dir'], 'bt_bt.yml')
        if not os.path.isfile(bt_fp):
            raise FileNotFoundError("Can't find your Beamtime yaml file.\n"
                                    "Did you accidentally delete it? "
                                    "Please contact beamline staff "
                                    "ASAP")
        bto = Beamtime.from_yaml(open(bt_fp))
        wavelength = bto.wavelength
    if detector is None:
        detector = 'perkin_elmer'
    if calibrant is None:
        calibrant = os.path.join(glbl['usrAnalysis_dir'], 'Ni24.D')
    c = Calibration(calibrant=calibrant, detector=detector,
                    wavelength=wavelength * 10 ** (-10))

    return c


def _collect_calib_img(exposure, dark_sub_bool, calibration_instance,
                       RE_instance, detector_calibration_server_uid):
    """helper function to collect calibration image and return it"""
    c = calibration_instance  # shorthand notation
    calibrant_name = c.calibrant.__repr__().split(' ')[0]
    calibration_dict = {'sample_name': calibrant_name,
                        'sample_composition': {calibrant_name: 1},
                        'is_calibration': True,
                        'detector_calibration_server_uid':
                        detector_calibration_server_uid}
    bto = RE_instance.beamtime  # grab beamtime object linked to run_engine
    sample = Sample(bto, calibration_dict)
    uid = RE_instance(sample, ScanPlan(bto, ct, exposure))
    light_header = xpd_configuration['db'][uid[-1]]  # last one must be light
    dark_uid = light_header.start.get('sc_dk_field_uid')
    dark_header = xpd_configuration['db'][dark_uid]

    dark_img = np.asarray(xpd_configuration['db'].get_images(
        dark_header, glbl['det_image_field'])).squeeze()

    img = np.asarray(xpd_configuration['db'].get_images(
        light_header, glbl['det_image_field'])).squeeze()

    if dark_sub_bool:
        img -= dark_img

    return img


def _save_and_attach_calib_param(calib_c, timestr,
                                 detector_calibration_server_uid):
    """save calibration parameters and attach to glbl class instance

    Parameters
    ----------
    calib_c : pyFAI.calibration.Calibration instance
        pyFAI Calibration instance with parameters after calibration
    time_str : str
        human readable time string
    calibration_uid : str
        uid associated with this calibration
    """
    # save glbl attribute for xpdAcq
    glbl['calib_config_dict'] = calib_c.geoRef.getPyFAI()
    glbl['calib_config_dict'].update(calib_c.geoRef.getFit2D())
    glbl['calib_config_dict'].update({'file_name':calib_c.basename})
    glbl['calib_config_dict'].update({'time':timestr})
    glbl['calib_config_dict'].update({'detector_calibration_server_uid':
                                      detector_calibration_server_uid})

    # save yaml dict used for xpdAcq
    yaml_name = glbl['calib_config_name']
    with open(os.path.join(glbl['config_base'], yaml_name), 'w') as f:
        yaml.dump(glbl['calib_config_dict'], f)

    print(calib_c.geoRef)
    print("INFO: End of calibration process. Your parameter set will be "
          "saved inside {}. this set of parameters will be injected "
          "as metadata to subsequent scans until you perform this "
          "process again".format(yaml_name))
    print("INFO: To save your calibration image as a tiff file run\n"
          "save_last_tiff()\nnow.")
    return


def _calibration(img, calibration, **kwargs):
    """engine for performing calibration on a image with geometry
    correction software. current backend is ``pyFAI``.

    Parameters
    ----------
    img : ndarray
        image to perfrom calibration process.
    calibration : pyFAI.calibration.Calibration instance
        pyFAI Calibration instance with wavelength, calibrant and
        detector configured.
    kwargs:
        additional keyword argument for calibration. please refer to
        pyFAI documentation for all options.
    """
    print('{:=^20}'.format("INFO: you are able to perform calibration, "
                           "please refer to pictorial guide here:\n"))
    print('{:^20}'
          .format("http://xpdacq.github.io/usb_Running.html#calib-manual\n"))
    # default params
    interactive = True
    dist = 0.1
    # calibration
    c = calibration  # shorthand notation
    timestr = _timestampstr(time.time())
    f_name = '_'.join([timestr, 'pyFAI_calib',
                       c.calibrant.__repr__().split(' ')[0]])
    w_name = os.path.join(glbl['config_base'], f_name)  # poni name
    poni_name = w_name + ".npt"
    c.gui = interactive
    c.basename = w_name
    c.pointfile = poni_name
    c.peakPicker = PeakPicker(img, reconst=True,
                              pointfile=poni_name,
                              calibrant=c.calibrant,
                              wavelength=c.wavelength,
                              **kwargs)
    c.peakPicker.gui(log=True, maximize=True, pick=True)
    update_fig(c.peakPicker.fig)
    c.gui_peakPicker()

    return c, timestr


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
                         'is_mask': True,
                         'mask_server_uid': mask_server_uid}
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

    # update global mask information
    glbl.update(dict(mask_server_uid=mask_server_uid))

    return
