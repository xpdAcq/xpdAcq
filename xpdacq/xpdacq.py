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

print('Before you start, make sure the area detector IOC is in "Continuous mode"')
pe1c_threshold = 300

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
    pe1c_frame_rate = 0.1  # FIXME - that should be heard from pe1c attributes
    pe1c_num_set = 1
    
    total_time = secs + mins*60
    num_frame = np.rint( total_time / pe1c_frame_rate )
    
    # logic to prevent from overflow
    if num_frame > pe1c_threshold:
        print('Overflow')
        pe1c_num_set = np.ceil( num_frame / pe1c_threshold)
        num_frame = pe1c_threshold
        # should we let user know??
    
    # FIXME - test if pe1c is correctly configured
    pe1c.number_of_sets.put(pe1c_num_set)
    pe1c.image_per_set.put(num_frame)

    # Set up plan
    print('Running a scan of %s minute(s) and %s second(s)' % (mins, secs))
    count_plan = Count([pe1], num=1)

    # reproduce QXRD workflow. Do dark and light scan in the same time so that we can subtract it
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
    # FIXME - make sure to plot the corrected image
    plot_last_one()
