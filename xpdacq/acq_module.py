## acquisition modlue

import numpy as np
import matplotlib.pyplot as plt

def get_light_images(scan_time = 1.0, scan_exposure_time = 0.2):
    from bluesky.scans import Count # create fake object
    from ophyd.detector import AreaDetector
        
    if scan_exposure_time > 5.0:
        print('Your exposure time is larger than 5 seconds. This can damage detector')
        print('Exposure time is set to 5 seconds')
        print('Number of exposures will be recalculated so that scan time is the same....')
        scan_exposure_time = 5.0
        num = int(np.rint(scan_time/scan_exposure_time))
    else:
        num = int(np.rint(scan_time/scan_exposure_time))
    print('Number of exposures is now %s' % num)
    if num == 0: num = 1 # at least one scan
    
    
    # configure pe1:
    pe1 = AreaDetector('pe1', scan_exposure_time)
    pe1.acquire_time = scan_exposure_time

    # configure scan:
    scan = Count([pe1], num)

    # FIXME: run scan with fake gs.RE()
    print('Now You run a scan')
    
    return
        
    
