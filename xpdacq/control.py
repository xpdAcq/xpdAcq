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

def _get_obj(name):
    ip = get_ipython() # build-in function
    return ip.user_ns[name]

def _open_shutter():
    ''' open the shutter that is currently working. Maintain at every beamtime
    ''' 
    import time
    
    # Shutter this time : shctl1
    sh_name = 'shctl1'
    sh = _get_obj(sh_name)
    
    print('Open shutter')
    #shutter status
    if sh.get() == 1:
        pass
    else:
        print('shutter value before open_pv.put(1): %s' % sh.get())
        # open shutter
        shutter_try = 0
        shutter_tries = 5
        while sh.get() == 0 and shutter_try < shutter_tries:
            sh.put(1)
            time.sleep(1.7)   
            print('shutter value after open_pv.put(1): %s' % sh.get())
            shutter_try += 1
        if sh.get() == 0:
            print('shutter failed to open after %i tries. Please check before continuing' % shutter_tries)
            return

    print('Shutter opened')

def _close_shutter():
    ''' close the shutter that is currently working. Maintain at every beamtime
    '''
    import time
    
    # Shutter this time : shctl1
    sh_name = 'shctl1'
    sh = _get_obj(sh_name)
    
    print('Close shutter')
    #shutter status
    if sh.get() == 0:
        pass
    else:
        print('shutter value before open_pv.put(0): %s' % sh.get())
        # open shutter
        shutter_try = 0
        shutter_tries = 5
        while sh.get() == 1 and shutter_try < shutter_tries:
            sh.put(0)
            time.sleep(1.7)   
            print('shutter value after open_pv.put(1): %s' % sh.get())
            shutter_try += 1
        if sh.get() == 1:
            print('shutter failed to close after %i tries. Please check before continuing' % shutter_tries)
            return

    print('Shutter closed')
