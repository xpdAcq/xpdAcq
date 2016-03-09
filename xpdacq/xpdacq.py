#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge, Tom Caswell
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
#
##############################################################################
import os
import yaml
import time
import datetime
import numpy as np
import copy
import sys
import uuid

from bluesky.plans import Count
from bluesky import Msg
from bluesky.plans import AbsScanPlan

from xpdacq.utils import _graceful_exit
from xpdacq.glbl import glbl
#from xpdacq.glbl import AREA_DET as area_det
#from xpdacq.glbl import TEMP_CONTROLLER as temp_controller
#from xpdacq.glbl import VERIFY_WRITE as verify_files_saved
#from xpdacq.glbl import LIVETABLE as LiveTable
from xpdacq.glbl import xpdRE
from xpdacq.beamtime import Union, Xposure
from xpdacq.control import _close_shutter, _open_shutter

print('Before you start, make sure the area detector IOC is in "Acquire mode"')


# top definition for minial impacts on the code. Can be changed later
area_det = glbl.area_det
LiveTable = glbl.LiveTable
temp_controller = glbl.temp_controller

def dryrun(sample,scan,**kwargs):
    '''same as run but scans are not executed.
    
    for testing.
    currently supported scans are "ct","tseries","Tramp" 
    where "ct"=count, "tseries=time series (series of counts)",
    and "Tramp"=Temperature ramp.

    '''
    cmdo = Union(sample,scan)
    #area_det = _get_obj('pe1c')
    parms = scan.md['sc_params']
    subs={}
    if 'subs' in parms: 
        subsc = parms['subs']
    for i in subsc:
        if i == 'livetable':
            subs.update({'all':LiveTable([area_det, temp_controller])})
        elif i == 'verify_write':
            subs.update({'stop':verify_files_saved})
   
    if scan.scan == 'ct':
       get_light_images_dryrun(cmdo,parms['exposure'],area_det, parms['subs'],**kwargs)
    elif scan.scan == 'tseries':
       collect_time_series_dryrun(scan,parms[0],area_det, **kwargs)
    elif scan.scan == 'Tramp':
        pass
    else:
       print('unrecognized scan type.  Please rerun with a different scan object')
       return
    
def _unpack_and_run(sample,scan,**kwargs):
    # check to see if wavelength has been set
    # bug
    #if not sample.md['bt_wavelength']:
        #sys.exit(_graceful_exit('Please have the instrument scientist set the wavelength value before proceeding.'))
    cmdo = Union(sample,scan)
    #area_det = _get_obj('pe1c')
    parms = scan.md['sc_params']
    subs={}
    if 'subs' in parms: subsc = parms['subs']
    for i in subsc:
        if i == 'livetable':
            subs.update({'all':LiveTable([area_det, temp_controller])})
        elif i == 'verify_write':
            subs.update({'stop':verify_files_saved})

    if scan.scan == 'ct':
        get_light_images(cmdo,parms['exposure'], area_det, subs,**kwargs)
    elif scan.scan == 'tseries':
        collect_time_series(cmdo,parms['exposure'], parms['delay'], parms['num'], area_det, subs, **kwargs)
    elif scan.scan == 'Tramp':
        collect_Temp_series(cmdo, parms['startingT'], parms['endingT'],parms['requested_Tstep'], parms['exposure'], area_det, subs, **kwargs)
    else:
        print('unrecognized scan type.  Please rerun with a different scan object')
        return

#### dark subtration code block ####

def _read_dark_yaml():
    dark_yaml_name = glbl.dk_yaml
    with open(dark_yaml_name, 'r') as f:
        dark_scan_list = yaml.load(f)
    return dark_scan_list 

def validate_dark(light_cnt_time, expire_time, dark_scan_list = None):
    ''' find the uid of appropriate dark inside dark_base
    
        Parameters
        ----------
        light_cnt_time : float
            exposure time of light image, expressed in seconds
        expire_time : float
            expire time of dark images, expressed in minute
        dark_scan_list : list, optional
            a list of dark dictionaries
        Returns
        -------
        dark_field_uid : str
            uid to qualified dark frame
    '''
    if not dark_scan_list: 
        dark_scan_list = _read_dark_yaml()
    if len(dark_scan_list) > 0:
        test_list = copy.copy(dark_scan_list)
        while time.time() - test_list[-1][2] < expire_time*60.:
            test = test_list.pop()
            if abs(test[1]-light_cnt_time) < 0.9*glbl.frame_acq_time: 
                return test[0] 
            elif len(test_list) == 0:
                return  None # scan list there but no good dark found
    else:
        return None # nothing in dark_scan_list. collect a dark

def _load_calibration(calibration_file_name = None):
    ''' function to load calibration file in config_base directory
    Parameters
    ----------
    calibration_file_name : str
    name of calibration file that are going to be used. if it is not specified, load the most recent one
    Returns
    -------
    config_dict : dict
    a dictionary containing calibration parameters calculated from SrXplanar
    '''
    config_dir = glbl.config_base
    f_list = [ f for f in os.listdir(config_dir) if f.endswith('cfg')]
    if not f_list:
        return # no config at all
    if calibration_file_name:
        config_in_use = calibration_file_name
    config_in_use = sorted(f_list, key=os.path.getmtime)[-1]
    config_timestamp = os.path.getmtime(config_in_use)
    config_time = datetime.datetime.fromtimestamp(config_timestamp).strftime('%Y%m%d-%H%M')
    config_dict = _load_config(os.path.join(config_dir,config_in_use))
    return (config_dict, config_in_use)

def _load_config(config_file_name):
    ''' help function to load config file '''
    config = ConfigParser()
    config.read(config_file_name)
    sections = config.sections()
    config_dict = {}
    for section in sections:
        config_dict[section] = {} # write down header
        options = config.options(section)
        for option in options:
            try:
                config_dict[section][option] = config.get(section, option)
                #if config_dict[option] == -1:
                # DebugPrint("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                config_dict[option] = None
    return config_dict


def prun(sample,scanplan,**kwargs):
    '''on this 'sample' run this 'scanplan'
        
    Arguments:
    sample - sample metadata object
    scanplan - scanplan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    if scanplan.shutter: 
        _open_shutter()
    scanplan.md.update({'xp_isprun':True})
    light_cnt_time = scanplan.md['sc_params']['exposure']
    expire_time = glbl.dk_window
    dark_field_uid = validate_dark(light_cnt_time, expire_time)
    if not dark_field_uid:
        dark_field_uid = dark(sample, scanplan)
        # remove is_dark tag in md
        dummy = scanplan.md.pop('xp_isdark') 
    scanplan.md['sc_params'].update({'dk_field_uid': dark_field_uid})
    scanplan.md['sc_params'].update({'dk_window':expire_time})
    try:
        (config_dict, config_name) = _load_calibration()
        scan.md.update({'xp_config_dict':config_dict})
        scan.md.update({'xp_config_name':config_name})
    except TypeError:
        print('INFO: No calibration config file found in config_base. Scan will continue.')
    if scanplan.shutter: 
        _open_shutter()
    _unpack_and_run(sample,scanplan,**kwargs)
    if scanplan.shutter: 
        _close_shutter()

def dark(sample,scan,**kwargs):
    '''on this 'scan' get dark images
    
    Arguments:
    sample - sample metadata object
    scan - scan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    print('collect dark frame now....')
    # print information to user since we might call dark during prun.
    dark_uid = str(uuid.uuid4())
    dark_exposure = scan.md['sc_params']['exposure']
    _close_shutter()
    scan.md.update({'xp_isdark':True})
    _unpack_and_run(sample,scan,**kwargs)
    dark_time = time.time() # get timestamp by the end of dark_scan 
    dark_def = (dark_uid, dark_exposure, dark_time)
    scan.md.update({'xp_isdark':False}) #reset
    _close_shutter()
    return dark_uid
    
def _yamify_dark(dark_def):
    dark_yaml_name = glbl.dk_yaml
    with open(dark_yaml_name, 'r') as f:
        dark_list = yaml.load(f)
    dark_list.append(dark_def)
    with open(dark_yaml_name, 'w') as f:
        yaml.dump(dark_list, f)

def setupscan(sample,scan,**kwargs):
    '''used for setup scans NOT production scans
     
    Scans run this way will get tagged with "setup_scan=True".  They
    will be saved for later retrieval but will be harder to search for
    in the database.
    Use prun() for production scans

    Arguments:
    sample - sample metadata object
    scan - scan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    if scan.shutter: _open_shutter()
    scan.md.update({'xp_isprun':False})
    _unpack_and_run(sample,scan,**kwargs)
    #parms = scan.sc_params
    if scan.shutter: _close_shutter()

def get_light_images(mdo, exposure = 1.0, det=area_det, subs_dict={}, **kwargs):
    '''the main xpdAcq function for getting an exposure
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    '''   
    
    # setting up detector
    #area_det = _get_obj(det)
    #glbl.area_det.number_of_sets.put(1)
    area_det.number_of_sets.put(1)
    area_det.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = area_det.cam.acquire_time.get()

    exp = Xposure(mdo)
    
    # compute number of frames and save metadata
    num_frame = int(exposure / acq_time)
    if num_frame == 0: 
        num_frame = 1
    computed_exposure = num_frame*acq_time
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':acq_time,'xp_num_frames':num_frame})
    
    area_det.images_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)
    
    plan = Count([area_det])
    xpdRE(plan,subs_dict,**md_dict)


def collect_Temp_series(mdo, Tstart, Tstop, Tstep, exposure = 1.0, det= area_det, subs_dict={}, **kwargs):
    '''the main xpdAcq function for getting a temperature series
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      T_start - flot - start setpoint of Temperature ramp
      
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    '''   
    #temp_controller = _get_obj('cs700')
    
    # setting up detector
    #area_det = _get_obj(det)
    area_det.number_of_sets.put(1)
    area_det.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = area_det.cam.acquire_time.get()

    exp = Xposure(mdo)
    
    # compute number of frames and save metadata
    num_frame = int(exposure / acq_time)
    if num_frame == 0: num_frame = 1
    computed_exposure = num_frame*acq_time
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':acq_time,'xp_num_frames':num_frame})
    
    Nsteps = _nstep(Tstart, Tstop, Tstep) # computed steps
    exp.md.update({'sc_startingT':Tstart,'sc_endingT':Tstop,'sc_requested_Tstep':Tstep}) 
    exp.md.update({'sc_Nsteps':Nsteps}) 
    #print('INFO: requested temperature step = ',Tstep,' -> computed temperature step:', _Tstep)
    # information is taking care in _nstep

    area_det.images_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)
        
    plan = AbsScanPlan([area_det], temp_controller, Tstart, Tstop, Nsteps)
    xpdRE(plan,subs_dict, **md_dict)

    print('End of collect_Temp_scans....')

def _nstep(start, stop, step_size):
    ''' return (start, stop, nsteps)'''
    requested_nsteps = abs((start - stop) / step_size)
    
    computed_nsteps = int(requested_nsteps)+1 # round down for finer step size
    computed_step_list = np.linspace(start, stop, computed_nsteps)
    computed_step_size = computed_step_list[1]- computed_step_list[0]
    print('INFO: requested temperature step size = ',step_size,' -> computed temperature step size:',abs(computed_step_size))
    return computed_nsteps

def collect_time_series(mdo, exposure=1.0, delay=0., num=1, det= area_det, subs_dict={}, **kwargs):
    """Collect a time series

    Any extra keywords are passed through to RE() as metadata

    Parameters
    ----------
    mdo : XPD
        Object to carry around the metadata
    num : int
        The number of points in the time series

    delay : float
        Time between starts of time points in [s].  If less than exposure, the
        exposure time will be maintained and this time will be increased.

    exposure : float, optional
        Total integration time per data point in [s]
    """
   
    # arrange md object
    exp = Xposure(mdo)
    #md_dict = exp.md
    #md_dict.update(kwargs)

    # get a local copy of md to update
    md = dict(exp.md)

    # grab the area detector
    #area_det = _get_obj(det)
    area_det.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = area_det.cam.acquire_time.get()

    # compute how many frames to collect
    num_frame = max(int(exposure / acq_time), 1)
    computed_exposure = num_frame * acq_time
    num_sets = 1
    
        
    real_delay = max(0, delay - computed_exposure)
    period = max(computed_exposure, real_delay + computed_exposure)
    # set how many frames to average
    area_det.images_per_set.put(num_frame)
    area_det.number_of_sets.put(num_sets)

    md.update({'requested_exposure': exposure,
               'computed_exposure': computed_exposure,
               'period': period})
    md.update({'time_per_frame': acq_time,
               'num_frames': num_frame,
               'number_of_sets': num_sets})
    md.update(kwargs)
    plan = Count([area_det], num=num, delay=real_delay)
    xpdRE(plan, subs_dict, **md)

    print('End of time series scan ....')


######## temporarily solution to user's unstoppable desire to SPEC-like behavior.... #########

def SPEC_Tseries_plan(detector, motor, start, stop, steps):
    yield Msg('open_run')
    for i in np.linspace(start, stop, steps):
        yield Msg('create')
        yield Msg('set', motor, i)
        yield Msg('read', motor)
        _open_shutter()
        yield Msg('trigger', detector)
        yield Msg('read', detector)
        _close_shutter()
        yield Msg('trigger', detector)
        yield Msg('read', detector)
        yield Msg('save')
    yield Msg('close_run')

def SPEC_Temp_series(mdo, Tstart, Tstop, Tstep, exposure = 1.0, det = area_det, subs_dict={}, **kwargs):
    '''the main xpdAcq function for getting an exposure
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      T_start - flot - start setpoint of Temperature ramp
      
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    '''   
    #temp_controller = _get_obj('cs700')
    
    # setting up detector
    area_det = _get_obj(det)
    area_det.number_of_sets.put(1)
    acq_time = area_det.cam.acquire_time.get()

    exp = Xposure(mdo)
    
    # compute number of frames and save metadata
    num_frame = int(exposure / acq_time)
    if num_frame == 0: num_frame = 1
    computed_exposure = num_frame*acq_time
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':acq_time,'xp_num_frames':num_frame})
    
    Nsteps = _nstep(Tstart, Tstop, Tstep) # computed steps
    exp.md.update({'sc_startingT':Tstart,'sc_endingT':Tstop,'sc_requested_Tstep':Tstep}) 
    exp.md.update({'sc_Nsteps':Nsteps}) 
    #print('INFO: requested temperature step = ',Tstep,' -> computed temperature step:', _Tstep)
    # information is taking care in _nstep

    area_det.images_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)
        
    plan = SPEC_Tseries_plan([area_det], temp_controller, Tstart, Tstop, Nsteps)
    xpdRE(plan,subs_dict, **md_dict)

    print('End of SPEC_Temp_scans....')
   
########################################################################################################

def get_bluesky_run(mdo, plan, det = area_det, subs_dict={}, **kwargs):
    '''An xpdAcq function for executing a custom (user defined) bluesky plan
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    '''   
    
    # setting up detector
    area_det = _get_obj(det)
#    area_det.number_of_sets.put(1)  # not sure about this one
    acq_time = area_det.cam.acquire_time.get()

    exp = Xposure(mdo)
    
    # compute number of frames and save metadata
    num_frame = int(exposure / acq_time)
    if num_frame == 0: num_frame = 1
    computed_exposure = num_frame*acq_time
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':acq_time,'xp_num_frames':num_frame})
    
    area_det.images_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)

    xpdRE(plan,subs_dict,**md_dict)



##########################################################
#    Dry Run thingys
######################################################
def get_light_images_dryrun(mdo, exposure = 1.0, det= area_det, subs_dict={}, **kwargs):
    '''the main xpdAcq function for getting an exposure
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    ''' 
    
    # default setting for pe1c
#    area_det = _get_obj('pe1c')
#    area_det.number_of_sets.put(1)

    exp = Xposure(mdo)
#    acq_time = area_det.cam.acquire_time.get()
    acq_time = 0.1
    
    # compute number of frames and save metadata
    num_frame = int(exposure/acq_time )
    if num_frame == 0: num_frame = 1
    computed_exposure = num_frame*acq_time
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':acq_time,'xp_num_frames':num_frame})
    
#    area_det.image_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)

    print('this will execute a single bluesky Count type scan')
    print('Sample: '+str(md_dict['sa_name']))
    print('[FIXME] more sample info here')
    print('using the "pe1c" detector (Perkin-Elmer in continuous acquisition mode)')
    print('The requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    print('in the form of '+str(num_frame)+' frames of '+str(acq_time)+' s summed into a single event')
    print('(i.e. accessible as a single tiff file)')
    print('')  
    print('The metadata saved with the scan will be:')
    print(md_dict)
    
def collect_time_series_dryrun(metadata_object, num, exposure=1.0, delay=0.,  **kwargs):
    """Collect a time series

    Any extra keywords are passed through to RE() as metadata

    Parameters
    ----------
    metadata_object : XPD
        Object to carry around the metadata
    num : int
        The number of points in the time series

    delay : float
        Time between starts of time points in [s].  If less than exposure, the
        exposure time will be maintained and this time will be increased.

    exposure : float, optional
        Total integration time per data point in [s]
    """
    # get a local copy of md to update
    md = dict(metadata_object.md)

    # grab the area detector
    #area_det = _get_obj('pe1c')

    acq_time = area_det.cam.acquire_time.get()

    # compute how many frames to collect
    num_frame = max(int(exposure / acq_time), 1)
    computed_exposure = num_frame * acq_time
    num_sets = 1

    est_writeout_ohead = 1.0
    real_delay = max(0, delay - computed_exposure)
    period = max(computed_exposure, real_delay + computed_exposure)
    # set how many frames to average
    area_det.image_per_set.put(num_frame)
    area_det.number_of_sets.put(num_sets)
    scan_length_s = period*num_sets
    m, s = divmod(scan_length_s, 60)
    h, m = divmod(m, 60)
    scan_length = str("%d:%02d:%02d" % (h, m, s))
    est_real_scan_length_s = (period+est_writeout_ohead)*num_sets
    m, s = divmod(est_real_scan_length_s, 60)
    h, m = divmod(m, 60)
    est_real_scan_length = str("%d:%02d:%02d" % (h, m, s))

    md.update({'requested_exposure': exposure,
               'computed_exposure': computed_exposure,
               'period': period})
    md.update({'time_per_frame': acq_time,
               'num_frames': num_frame,
               'number_of_sets': num_sets})
    md.update(kwargs)

    
    print('this will execute a series of'+str(num)+' bluesky Count type scans')
    print('Sample: '+md['sa_name'])
    print('[FIXME] more sample info here')
    print('using the "pe1c" detector (Perkin-Elmer in continuous acquisition mode)')
    print('The requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    print('in the form of '+str(num_frame)+' frames of '+str(acq_time)+' s summed into a single event')
    print('(i.e. accessible as a single tiff file)')
    print('')
    print('There will be a delay of '+str(real_delay)+' (compared to the requested delay of '+str(delay)+') s')
    print('This will result in a nominal period (neglecting readout overheads) of '+str(period)+' s')
    print('Which results in a total scan time of '+str(scan_length))
    print('Using an estimated write-out overhead of '+str(est_writeout_ohead)+' this gives and estimated total scan length of '+str(est_real_scan_length))
    print('Real outcomes may vary!')
    print('that will be summed into a single event (e.g. accessible as a single tiff file)')
    print('')
    print('The metadata saved with the scan will be:')
    print(md_dict)

#    plan = Count([area_det], num=num, delay=real_delay)
#    return gs.RE(plan, **md)

################# private module ###########################
"""
def _bluesky_global_state():
    '''Import and return the global state from bluesky.'''

    from bluesky.standard_config import gs
    return gs
    
def _bluesky_metadata_store():
    '''Return the dictionary of bluesky global metadata.'''

    gs = _bluesky_global_state()
    return gs.RE.md

def _bluesky_RE():
    import bluesky
    from bluesky.run_engine import RunEngine
    from bluesky.register_mds import register_mds
    #from bluesky.run_engine import DocumentNames
    RE = RunEngine()
    register_mds(RE)
    return RE

RE = _bluesky_RE()
gs = _bluesky_global_state()

old_validator = RE.md_validator
def ensure_sc_uid(md):
    old_validator(md)
    if 'sc_uid' not in md:
        raise ValueError("scan metadata needed to run scan.  Please create a scan metadata object and rerun.")
RE.md_validator = ensure_sc_uid
"""

##############################################################
'''
def _xpd_plan_1(num_saturation, num_unsaturation, det=None):
    's' type-1 plan: change image_per_set on the fly with Count
    
    Parameters:
    -----------
        num_img : int
            num of images you gonna take, last one is fractional
        
        time_dec : flot
    ''s'
    from bluesky import Msg
    from xpdacq.control import _get_obj
    
    if not det:
        _det = _get_obj('pe1c')

    num_threshold = int(expo_threshold / frame_rate)
    print('Overflow...')
    print('num of threshold = %i ' % num_threshold)

    yield Msg('open_run')
    yield Msg('stage', _det)
    _det.number_of_sets.put(1)
    _det.images_per_set.put(num_threshold)
    for i in range(num_saturation+1):
        yield Msg('create')
        yield Msg('trigger', _det)
        yield Msg('read', _det)
        yield Msg('save')
    
    _det.images_per_set.put(num_unsaturation)
    yield Msg('create')
    yield Msg('trigger', _det)
    yield Msg('read', _det)
    yield Msg('save')
    yield Msg('unstage', _det)
    yield Msg('close_run')


# reproduce QXRD workflow. Do dark and light scan with the same amount of time so that we can subtract it
# can be modified if we have better understanding on dark current on area detector    
   
    
def QXRD_plan():
    print('Collecting dark frames....')
    _close_shutter()
    yield from count_plan
    print('Collecting light frames....')
    _open_shutter()
    yield from count_plan

        
    # hook to visualize data
    # FIXME - make sure to plot dark corrected image
    plot_scan(db[-1])

'''
