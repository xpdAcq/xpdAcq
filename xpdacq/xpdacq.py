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
def _get_obj(name):
    ip = get_ipython() # build-in function
    return ip.user_ns[name]

import numpy as np
from xpdacq.beamtime import Union, Xposure
from bluesky.plans import Count
from bluesky import Msg
from xpdacq.control import _get_obj   
from xpdacq.control import _open_shutter
from xpdacq.control import _close_shutter
from xpdacq.analysis import *
from bluesky.plans import AbsScanPlan

xpdRE = _get_obj('xpdRE')
LiveTable = _get_obj('LiveTable')

print('Before you start, make sure the area detector IOC is in "Acquire mode"')
#expo_threshold = 60 # in seconds Deprecated!
FRAME_ACQUIRE_TIME = 0.1 
AREA_DET_NAME = 'pe1c'
TEMP_CONTROLLER_NAME = 'cs700'

# set up the detector    
# default settings for pe1c
area_det = _get_obj(AREA_DET_NAME)
area_det.cam.acquire_time.put(FRAME_ACQUIRE_TIME)
temp_controller = _get_obj(TEMP_CONTROLLER_NAME)


def dryrun(sample,scan,**kwargs):
    '''same as run but scans are not executed.
    
    for testing.
    currently supported scans are "ct","tseries","Tramp" 
    where "ct"=count, "tseries=time series (series of counts)",
    and "Tramp"=Temperature ramp.

    '''
    cmdo = Union(sample,scan)
    area_det = _get_obj('pe1c')
    parms = scan.md['sc_params']
    subs={}
    if 'subs' in parms: subsc = parms['subs']
    for i in subsc:
        if i == 'livetable':
            subs.update({'all':LiveTable([area_det, temp_controller])})
        elif i == 'verify_write':
            subs.update({'stop':verify_files_saved})
   
    if scan.scan == 'ct':
       get_light_images_dryrun(cmdo,parms['exposure'],'pe1c',parms['subs'],**kwargs)
    elif scan.scan == 'tseries':
       collect_time_series_dryrun(scan,parms[0],'pe1c',**kwargs)
    elif scan.scan == 'Tramp':
        pass
    else:
       print('unrecognized scan type.  Please rerun with a different scan object')
       return
    
def _unpack_and_run(sample,scan,**kwargs):
    cmdo = Union(sample,scan)
    area_det = _get_obj('pe1c')
    parms = scan.md['sc_params']
    subs={}
    if 'subs' in parms: subsc = parms['subs']
    for i in subsc:
        if i == 'livetable':
            subs.update({'all':LiveTable([area_det, temp_controller])})
        elif i == 'verify_write':
            subs.update({'stop':verify_files_saved})

    if scan.scan == 'ct':
       get_light_images(cmdo,parms['exposure'],'pe1c',subs,**kwargs)
    elif scan.scan == 'tseries':
       collect_time_series(cmdo,parms['exposure'], parms['delay'], parms['num'],'pe1c', subs, **kwargs)
    elif scan.scan == 'Tramp':
        collect_Temp_series(cmdo, parms['startingT'], parms['endingT'],parms['requested_Tstep'], parms['exposure'], 'pe1c', subs, **kwargs)
    else:
       print('unrecognized scan type.  Please rerun with a different scan object')
       return

def prun(sample,scan,**kwargs):
    '''on this 'sample' run this 'scan'
        
    Arguments:
    sample - sample metadata object
    scan - scan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    if scan.shutter: _open_shutter()
    scan.md.update({'xp_isprun':True})
    _unpack_and_run(sample,scan,**kwargs)
    #parms = scan.sc_params
    if scan.shutter: _close_shutter()

def dark(sample,scan,**kwargs):
    '''on this 'scan' get dark images
    
    Arguments:
    sample - sample metadata object
    scan - scan metadata object
    **kwargs - dictionary that will be passed through to the run-engine metadata
    '''
    _close_shutter()
    scan.md.update({'xp_isdark':True})
    _unpack_and_run(sample,scan,**kwargs)
    _close_shutter()
   
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

def get_light_images(mdo, exposure = 1.0, det='pe1c', subs_dict={}, **kwargs):
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
    
    area_det.images_per_set.put(num_frame)
    md_dict = exp.md
    md_dict.update(kwargs)
    
    plan = Count([area_det])
    xpdRE(plan,subs_dict,**md_dict)

    print('End of get_light_image...')


def collect_Temp_series(mdo, Tstart, Tstop, Tstep, exposure = 1.0, det='pe1c', subs_dict={}, **kwargs):
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
    temp_controller = _get_obj('cs700')
    
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

def collect_time_series(mdo, exposure=1.0, delay=0., num=1, det='pe1c', subs_dict={}, **kwargs):
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
    area_det = _get_obj(det)

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

def SPEC_Temp_series(mdo, Tstart, Tstop, Tstep, exposure = 1.0, det='pe1c', subs_dict={}, **kwargs):
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
    temp_controller = _get_obj('cs700')
    
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

def get_bluesky_run(mdo, plan, det='pe1c', subs_dict={}, **kwargs):
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
def get_light_images_dryrun(mdo, exposure = 1.0, det='pe1c', subs_dict={}, **kwargs):
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
