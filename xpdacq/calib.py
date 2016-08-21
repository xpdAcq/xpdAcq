""" Script to perform pyFAI calibration in pure Python """
import os
import time
import yaml
import logging
import datetime
import numpy as np
from IPython import get_ipython

import tifffile as tif

from .glbl import glbl
from .beamtime import ScanPlan, ct

# Hot fix at beamline
from databroker import get_images

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
            raise NameError("Required object {} doesn't exit in"
                            "namespace".format(obj_str))
    return

def _timestampstr(timestamp):
    ''' convert timestamp to strftime formate '''
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d-%H%M')
    return timestring

def run_calibration(exposure=60, calibrant_file=None, wavelength=None,
                    detector=None, gaussian=None):
    """ function to collect calibration image, run calibration process and
     store calibration parameters into xpdUser/config_base/

    Parameters
    ----------
    exposure : int
        optional. total exposure time in sec. default is 60s
    calibrant_name : str
        optional.name of calibrant used, different calibrants correspond to 
        different d-spacing profiles. Default is 'Ni'. User can assign 
        different calibrant, given d-spacing file path presents
    wavelength : flot [unit :angstrom]
        optional.wavelength of x-ray being used in angstrom Default value is 
        read out from existing xpdacq.Beamtime object
    detector : pyfai.detector.Detector
        optional. instance of detector which defines pxiel size in x- or
        y-direction. default is set to Perkin Elmer detector
    gaussian : int
        optional. gaussian width between rings, default is 100.
    """
    # default params
    interactive = True 
    dist = 0.1

    _check_obj(_REQUIRED_OBJ_LIST)
    ips = get_ipython()
    bto = ips.ns_table['user_global']['bt']
    prun = ips.ns_table['user_global']['prun']
    #print('*** current beamtime info = {} ***'.format(bto.md))
    calibrant = Calibrant()
    # d-spacing
    if calibrant_file is not None:
        calibrant.load_file(calibrant_file)
        calibrant_name = os.path.split(calibrant_file)[1]
        calibrant_name = os.path.splitext(calibrant_name)[0]
    else:
        calibrant.load_file(os.path.join(glbl.usrAnalysis_dir, 'Ni24.D'))
        calibrant_name = 'Ni'
    # wavelength
    if wavelength is None:
        _wavelength = bto['bt_wavelength']
    else:
        _wavelength = wavelength
    calibrant.wavelength = _wavelength*10**(-10)
    # detector
    if detector is None:
        detector = Perkin()
    # scan
    calibration_dict = {'sample_name':calibrant_name,
                        'sample_composition':{calibrant_name :1}}
                        # simplified version of Sample object
    prun_uid = prun(calibration_dict, ScanPlan(bto, ct, exposure))
    light_header = glbl.db[prun_uid[-1]] # last one is always light
    dark_uid = light_header.start['sc_dk_field_uid']
    dark_header = glbl.db[dark_uid]
    # unknown signature of get_images
    dark_img = np.asarray(get_images(dark_header, glbl.det_image_field)).squeeze()
    #dark_img = np.asarray(glbl.get_images(dark_header, glbl.det_image_field)).squeeze()
    for ev in glbl.get_events(light_header, fill=True):
        img = ev['data'][glbl.det_image_field]
        img -= dark_img
    # calibration
    timestr = _timestampstr(time.time())
    basename = '_'.join(['pyFAI_calib', calibrant_name, timestr])
    w_name = os.path.join(glbl.config_base, basename) # poni name
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
                              #method=method)
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
    # update untile next time
    glbl.calib_config_dict = c.ai.getPyFAI()
    Fit2D_dict = c.ai.getFit2D()
    glbl.calib_config_dict.update(Fit2D_dict)
    glbl.calib_config_dict.update({'file_name':basename})
    glbl.calib_config_dict.update({'time':timestr})
    # write yaml
    yaml_name = glbl.calib_config_name
    with open(os.path.join(glbl.config_base, yaml_name),'w') as f:
        yaml.dump(glbl.calib_config_dict, f)

    return c.ai
