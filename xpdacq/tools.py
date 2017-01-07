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
import os
import sys
from time import strftime
from IPython import get_ipython

def _graceful_exit(error_message):
    try:
        raise RuntimeError(error_message)
        return 0
    except Exception as err:
        sys.stderr.write('WHOOPS: {}'.format(str(err)))
        return 1


def _check_obj(obj_name, error_msg=None):
    """ function to check if an object exists in current namespace

    Parameter
    ---------
    obj_name : str
        object name in string format
    error_msg : str
        error msg when target object can't be found in current
        namespace
    """
    if error_msg is None:
        error_msg = "Required object {} doesn't exist in"\
                    "current namespace".format(obj_name)
    ips = get_ipython()
    if not ips.ns_table['user_global'].get(obj_name, None):
        raise NameError(error_msg)
    return


def _timestampstr(timestamp):
    """ convert timestamp to strftime formate """
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        '%Y%m%d-%H%M%S')
    return timestring


def _RE_state_wrapper(RE_obj):
    """ a wrapper to check state of bluesky runengine object after pausing

        it provides control to stop/abort/resume runengine under current package structure
    """
    usr_input = input('')
    # while loop gives chance to iteratively confirm user's input
    while RE_obj.state == 'paused':
        if usr_input in 'resume()':
            RE_obj.resume()
        elif usr_input in 'abort()':
            abort_all = input(
                '''current scan will be aborted. Do you want to abort all successive scans (if you are running a script)? y/[n]  ''')
            while True:
                if abort_all in ('y', 'yes'):
                    sys.exit(_graceful_exit(
                        '''INFO: All successive scans are aborted'''))
                elif abort_all in ('n', 'no'):
                    print(
                        '''INFO: Current scan is aborted and successive ones are kept''')
                    RE_obj.abort()
                else:
                    print('please reenter your input')
        elif usr_input in 'stop()':
            RE_obj.stop()
        else:
            print('please renter your input')
