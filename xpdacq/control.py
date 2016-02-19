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
#def _get_obj(name):
    #ip = get_ipython() # build-in function
    #return ip.user_ns[name]

#shctl1 = _get_obj('shctl1')

from xpdacq.config import shctl1

def _open_shutter():
    shctl1.put(1)
    while True:
        if shctl1.get():
            break
            time.sleep(0.5)
    return 
           
def _close_shutter():
    shctl1.put(0)
    while True:
        if not shctl1.get():
            break
            time.sleep(0.5)
    return        
