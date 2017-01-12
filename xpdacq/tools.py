"""module to store tools which use standard libraries only"""
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
import sys
import datetime
from time import strftime
from IPython import get_ipython

class xpdAcqException(Exception):

    """
    customized class for xpdAcq-related exception
    """

    pass


def _graceful_exit(error_message):
    try:
        raise RuntimeError(error_message)
        return 0
    except Exception as err:
        sys.stderr.write('WHOOPS: {}'.format(str(err)))
        return 1


def _check_obj(obj_name, error_msg=None):
    """function to check if an object exists in current namespace

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
    """convert timestamp to strftime formate"""
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        '%Y%m%d-%H%M%S')
    return timestring
