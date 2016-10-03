""" Script to perform pyFAI calibration in pure Python """
import os
import uuid
import time
import yaml
import logging
import datetime
import numpy as np
from IPython import get_ipython

#FIXME : this import is intentionally left as we will save calib_img
#FIXME : leave for separate PR
import tifffile as tif

from .glbl import glbl
from .beamtime import ScanPlan, Sample, ct
from xpdan.tools import mask_img

from pyFAI.gui_utils import update_fig
from pyFAI.detectors import Perkin, Detector
from pyFAI.calibration import Calibration, PeakPicker
from pyFAI.calibrant import Calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

_REQUIRED_OBJ_LIST = ['prun', 'bt']


def _check_obj(required_obj_list):
    """ function to check if object(s) exist

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
    """ convert timestamp to strftime formate """
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        '%Y%m%d-%H%M')
    return timestring


def run_calibration(exposure=60, dark_sub=True, calibrant_file=None,
                    wavelength=None, detector=None, gaussian=None):

    """ function to run entire calibration process.

    Entire process includes: collect calibration image, trigger pyFAI 
    calibration process, store calibration parameters as a yaml file 
    under xpdUser/config_base/ and inject uid of calibration image to
    following scans, until this function is run again.

    Parameters
    ----------
    exposure : int, optional
        total exposure time in sec. Default is 60s
    dark_sub : bool, optional
        option of turn on/off dark subtraction on this calibration
        image. default is True.
    calibrant_file : str, optional
        calibrant file being used, default is 'Ni.D' under 
        xpdUser/userAnalysis/. File name except for extention will be 
        used as sample name.
    wavelength : flot, optional
        current of x-ray wavelength, in angstrom. Default value is 
        read out from existing xpdacq.Beamtime object
    detector : pyfai.detector.Detector, optional.
        instance of detector which defines pxiel size in x- and
        y-direction. Default is set to Perkin Elmer detector
    gaussian : int, optional
        gaussian width between rings, Default is 100.
    """

    _check_obj(_REQUIRED_OBJ_LIST)
    ips = get_ipython()
    bto = ips.ns_table['user_global']['bt']
    prun = ips.ns_table['user_global']['prun']

    # d-spacing
    if calibrant_file is not None:
        calibrant_name = os.path.split(calibrant_file)[1]
        calibrant_name = os.path.splitext(calibrant_name)[0]
    else:
        calibrant_name = 'Ni'

    # scan
    calib_collection_uid = str(uuid.uuid4())
    calibration_dict = {'sample_name':calibrant_name,
                        'sample_composition':{calibrant_name :1},
                        'is_calibration': True,
                        'calibration_collection_uid': calib_collection_uid}
    sample = Sample(bto, calibration_dict)
    prun_uid = prun(sample, ScanPlan(bto, ct, exposure))
    light_header = glbl.db[-1]
    if dark_sub:
        dark_uid = light_header.start['sc_dk_field_uid']
        dark_header = glbl.db[dark_uid]
        dark_img = np.asarray(glbl.db.get_images(dark_header,
                                glbl.det_image_field)).squeeze()
    for ev in glbl.db.get_events(light_header, fill=True):
        img = ev['data'][glbl.det_image_field]
        if dark_sub:
            img -= dark_img

    print('{:=^20}'.format("INFO: you are able to calib, please refer"
                           "to guid here:\n"))
    print('{:^20}'
          .format("http://xpdacq.github.io/usb_Running.html#calib-manual"))
    print()
    # calibration, return a azimuthal integrator
    ai = calibration(img, calibrant_file=calibrant_file,
                     calib_collection_uid=calib_collection_uid,
                     wavelength=wavelength, detector=detector,
                     gaussian=gaussian)

    # save glbl attribute for xpdAcq
    timestr = _timestampstr(time.time())
    basename = '_'.join(['pyFAI_calib', calibrant_name, timestr])
    glbl.calib_config_dict = ai.getPyFAI()
    Fit2D_dict = ai.getFit2D()
    glbl.calib_config_dict.update(Fit2D_dict)
    glbl.calib_config_dict.update({'file_name':basename})
    glbl.calib_config_dict.update({'time':timestr})
    # FIXME: need a solution for selecting desired calibration image
    # based on calibration_collection_uid later
    glbl.calib_config_dict.update({'calibration_collection_uid':
                                   calib_collection_uid})
    # save yaml dict used for xpdAcq
    yaml_name = glbl.calib_config_name
    with open(os.path.join(glbl.config_base, yaml_name), 'w') as f:
        yaml.dump(glbl.calib_config_dict, f)

    return ai


def run_mask_builder(exposure=300, dark_sub=True,
                     poloarization_factor=0.99,
                     sample_name=None, calib_dict=None,
                     mask_dict=None, save_name=None):
    """ function to generate mask

    this function will execute a count scan and generate a mask based on
    image collected from this scan.

    Parameters
    ----------
    exposure : float, optional
        exposure time of this scan. default is 300s.
    dark_sub : bool, optional
        turn on/off of dark subtraction. default is True.
    poloarization_factor: float, optional.
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
        full path for this mask going to be saved. if it is None, only
        the mask object will be returned, no file will be saved locally.

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
    prun = ips.ns_table['user_global']['prun']

    # default behavior
    if sample_name is None:
        sample_name = 'mask_target'

    if mask_dict is None:
        mask_dict = glbl.mask_dict

    if calib_dict is None:
        calib_dict = glbl.calib_config_dict

    # setting up geometry parameters
    ai = AzimuthalIntegrator()
    ai.setPyFAI(**calib_dict)

    # scan
    mask_collection_uid = str(uuid.uuid4())
    mask_builder_dict = {'sample_name':sample_name,
                        'sample_composition':{sample_name :1},
                        'is_mask': True,
                        'mask_collection_uid': mask_collection_uid}
    sample = Sample(bto, mask_builder_dict)
    prun_uid = prun(sample, ScanPlan(bto, ct, exposure))
    light_header = glbl.db[-1]
    if dark_sub:
        dark_uid = light_header.start['sc_dk_field_uid']
        dark_header = glbl.db[dark_uid]
        dark_img = np.asarray(glbl.db.get_images(dark_header,
                                glbl.det_image_field)).squeeze()
    for ev in glbl.db.get_events(light_header, fill=True):
        img = ev['data'][glbl.det_image_field]
        if dark_sub:
            img -= dark_img

    print("INFO: masking you image ....")
    img /= ai.polarization(img.shape, polarization_factor)
    mask = mask_img(img, ai, **mask_dict)
    print("INFO: add mask to global state")
    glbl.mask = mask

    if save_name is not None:
        np.save(mask, save_name)

    return mask


def calibration(img, calibrant_file=None, wavelength=None,
                calib_collection_uid=None, save_file_name=None,
                detector=None, gaussian=None):
    """ run calibration process on a image with geometry correction
    software

    current backend is ``pyFAI``.

    Parameters
    ----------
    img : ndarray
        image to be calibrated
    calibrant_file : str, optional
        calibrant file being used, default is 'Ni.D' under 
        xpdUser/userAnalysis/
    wavelength : flot, optional
        current of x-ray wavelength, in angstrom. Default value is 
        read out from existing xpdacq.Beamtime object
    calibration_collection_uid : str, optional
        uid of calibration collection. default is generated from run
        calibration
    save_file_name : str, optional
        file name for yaml that carries resultant calibration parameters
    detector : pyfai.detector.Detector, optional.
        instance of detector which defines pixel size in x- and
        y-direction. Default is set to Perkin Elmer detector
    gaussian : int, optional
        gaussian width between rings, Default is 100.
    """
    # default params
    interactive = True
    dist = 0.1

    _check_obj(_REQUIRED_OBJ_LIST)
    ips = get_ipython()
    bto = ips.ns_table['user_global']['bt']
    prun = ips.ns_table['user_global']['prun']

    calibrant = Calibrant()
    # d-spacing
    if calibrant_file is not None:
        calibrant.load_file(calibrant_file)
        calibrant_name = os.path.split(calibrant_file)[1]
        calibrant_name = os.path.splitext(calibrant_name)[0]
    else:
        calibrant.load_file(os.path.join(glbl.usrAnalysis_dir, 'Ni.D'))
        calibrant_name = 'Ni'
    # wavelength
    if wavelength is None:
        _wavelength = bto['bt_wavelength']
    else:
        _wavelength = wavelength
    calibrant.wavelength = _wavelength * 10 ** (-10)
    # detector
    if detector is None:
        detector = Perkin()
    # calibration
    timestr = _timestampstr(time.time())
    basename = '_'.join(['pyFAI_calib', calibrant_name, timestr])
    w_name = os.path.join(glbl.config_base, basename)  # poni name
    c = Calibration(wavelength=calibrant.wavelength,
                    detector=detector,
                    calibrant=calibrant,
                    gaussianWidth=gaussian)
    c.gui = interactive
    c.basename = w_name
    c.pointfile = w_name + ".npt"
    c.ai = AzimuthalIntegrator(dist=dist, detector=detector,
                               wavelength=calibrant.wavelength)
    c.peakPicker = PeakPicker(img, reconst=True, mask=detector.mask,
                              pointfile=c.pointfile, calibrant=calibrant,
                              wavelength=calibrant.wavelength)
    # method=method)
    if gaussian is not None:
        c.peakPicker.massif.setValleySize(gaussian)
    else:
        c.peakPicker.massif.initValleySize()

    if interactive:
        c.peakPicker.gui(log=True, maximize=True, pick=True)
        update_fig(c.peakPicker.fig)
    c.gui_peakPicker()
    c.ai.setPyFAI(**c.geoRef.getPyFAI())
    c.ai.wavelength = c.geoRef.wavelength

    return c.ai
