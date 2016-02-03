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
## testing section ##
from bluesky.plans import Count # fake object but exact syntax
#####################

import numpy as np
import matplotlib.pyplot as plt

from xpdacq.control import _get_obj

from dataportal import DataBroker as db

print('Before you start, make sure the area detector IOC is in "Continuous mode"')
expo_threshold = 60 # in seconds
frame_rate = 0.1 # default frame rate
area_det_name = 'pe1c'
area_det = _get_obj(area_det_name)


################# private module ###########################
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

##############################################################

def get_light_images(secs = 1.0, mins = 0):
    
    # TODO - finalize the format of scan time input
    ''' simple function that wrap Count
    
    Parameters
    -----------
    secs - float
        exposure time

    mins - float
        exposure time

    Returns
    --------
    It returns nothing

    '''
    
    from bluesky.plans import Count
    from xpdanl.xpdanl import plot_last_one

    # FIXME - proper command to close and open shutter
    from xpdacq.control import _open_shutter
    from xpdacq.control import _close_shutter
    
    # default setting for pe1c
    area_det.cam.acquire_time.put(frame_rate)

    # set to number we want
    pe1c.cam.acquire_time.put(0.1)

    pe1c_num_set = 1
    
    total_time = secs + mins*60.
    
    # logic to prevent from overflow
    frame_info = _cal_frame(total_time)
    
    if frame_info[0] == 0:
        # no saturation
        num_img = 1 
        area_det.number_of_sets.put(num_img)
        
        num_frame = frame_info[1]
        area_det.image_per_set.put(num_frame)
        plan = Count([area_det], num= num_frame)
        gs.RE(plan)
        
    if frame_info[0] != 0:
        num_img = frame_info[0] + 1
        gs.RE(_xpd_plan_1(frame_info[0], frame_info[1]))
    
    print('End of get_light_image...')

def _xpd_plan_1(num_saturation, num_unsaturation, det=None):
    ''' type-1 plan: change image_per_set on the fly with Count
    
    Parameters:
    -----------
        num_img : int
            num of images you gonna take, last one is fractional
        
        time_dec : flot
    '''
    from bluesky import Msg
    from xpdacq.control import _get_obj
    
    if not det:
        _det = _get_obj('pe1c')

    num_threshold = int(expo_threshold / frame_rate)

    yield Msg('open_run')
    yield Msg('stage', _det)
    _det.number_of_sets.put(1)
    
    _det.image_per_set.put(num_threshold)
    for i in range(num_saturation):
        yield Msg('create')
        yield Msg('trigger', _det)
        yield Msg('read', _det)
        yield Msg('save')
    
    _det.image_per_set.put(num_unsaturation)
    yield Msg('create')
    yield Msg('trigger', _det)
    yield Msg('read', _det)
    yield Msg('save')
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

    RE(QXRD_plan())
    
        
    # hook to visualize data
    # FIXME - make sure to plot dark corrected image
    plot_scan(db[-1])

def _cal_frame(total_time):
    ''' function to calculate frame
        
        Parameters
        ----------
        total_time : float
            - total time in seconds
        
        frame_rate : float
            - 'unit' of exposure   
    
        Returns
        -------
        out_put : tuple
            - (integer, fractional number)

    '''
    import math    
    total_float = total_time / expo_threshold
    parsed_num = math.modf(total_float)
    
    # number of frames that will collect with maximum exposure
    num_int = parsed_time[1]
    
    # last frame, collect fractio of exposure threshold
    num_dec = (parsed_time[0] * expo_threshold) / frame_rate
    
    return (num_int, num_dec)
