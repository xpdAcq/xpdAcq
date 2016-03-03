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
#from xpdacq.glbl import SHUTTER as shutter
from xpdacq.glbl import glbl
import time

shutter = glbl.shutter


def _open_shutter():
    shutter.put(1)
    while True:
        if shutter.get():
            break
        time.sleep(0.5)
    return 
           
def _close_shutter():
    shutter.put(0)
    while True:
        if not shutter.get():
            break
        time.sleep(0.5)
    return        
