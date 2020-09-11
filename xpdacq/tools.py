"""module to store tools which use standard libraries only"""
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
import warnings
from time import strftime
from IPython import get_ipython
import copy


def regularize_dict_key(input_dict: dict, target_chr: str, replace_chr: str) -> dict:
    """recursively replace target character in keys with desired one. Return a new dictionary.

    Parameters
    ----------
    input_dict : dict
        a dictionary going to be cleaned. it can be nested
    target_chr : str
        character that will be replaced
    replace_chr : str
        character that is going to replace target character
    """
    dct = dict()
    for k, v in copy.deepcopy(input_dict).items():
        if isinstance(k, str) and target_chr in k:
            print(
                "replacing character {} with character {} "
                "in dictionary".format(target_chr, replace_chr)
            )
            k = k.replace(target_chr, replace_chr)
        if isinstance(v, dict):
            v = regularize_dict_key(v, target_chr, replace_chr)
        dct[k] = v
    return dct


def validate_dict_key(input_dict, invalid_chr, suggested_chr):
    """
    recursively go through a nested dict and collect keys
    contains invalid character

    Parameters
    ----------
    input_dict : dict
        a dictionary going to be inspected. it can be nested.
    invalid_chr : str
        invalid character for key name
    suggested_chr : str
        suggested character to replace invalid_chr
    """
    invalid_key_list = []
    for k, v in input_dict.items():
        if isinstance(v, dict):
            if isinstance(k, str) and invalid_chr in k:
                invalid_key_list.append(k)
            validate_dict_key(v, invalid_chr, suggested_chr)
        else:
            if isinstance(k, str) and invalid_chr in k:
                invalid_key_list.append(k)
    if invalid_key_list:
        raise RuntimeError(
            "Sadly our database can't digest periods in "
            "dictionary keys. We have found a number of "
            "entries in your spreadsheet that will "
            "violate this. these are listed below:\n{}\n"
            "As annoying as this is, we suggest you change "
            "the sample name to remove the {} characters,"
            " for example, you could replace {} with {} in "
            "your spreadsheet.".format(
                invalid_key_list, invalid_chr, invalid_chr, suggested_chr
            )
        )


class xpdAcqException(Exception):
    """
    customized class for xpdAcq-related exception
    """

    pass


class xpdAcqError(xpdAcqException):
    """
    customized error for xpaAcq-related error
    """

    pass

def _graceful_exit(error_message):
    try:
        raise RuntimeError(error_message)
        return 0
    except Exception as err:
        sys.stderr.write("WHOOPS: {}".format(str(err)))
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
        error_msg = (
            "Required object {} doesn't exist in"
            "current namespace".format(obj_name)
        )
    ips = get_ipython()
    obj = ips.ns_table["user_global"].get(obj_name, None)
    if not obj:
        raise NameError(error_msg)
    else:
        return obj


def _timestampstr(timestamp):
    """convert timestamp to strftime formate"""
    timestring = datetime.datetime.fromtimestamp(float(timestamp)).strftime(
        "%Y%m%d-%H%M%S"
    )
    return timestring
