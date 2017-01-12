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
import warnings

def regularize_dict_key(input_dict, target_chr, replace_chr):
    """recursively replace target character in keys with desired one

    Parameters
    ----------
    input_dict : dict
        a dictionary going to be cleaned. it can be nested
    target_chr : str
        character that will be replaced
    replace_chr : str
        character that is going to replace target character
    """
    for k, v in input_dict.items():
        if isinstance(v, dict):
            if isinstance(k, str) and target_chr in k:
                print("replacing character {} with character {} "
                      "in dictionary".format(target_chr, replace_chr))
                clean_k = k.replace(target_chr, replace_chr)
                input_dict[clean_k] = input_dict.pop(k)
            regularize_dict_key(v, target_chr, replace_chr)
        else:
            if isinstance(k, str) and target_chr in k:
                print("replacing character {} with character {} "
                      "in dictionary".format(target_chr, replace_chr))
                clean_k = k.replace(target_chr, replace_chr)
                input_dict[clean_k] = input_dict.pop(k)


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
        raise RuntimeError("Sadly our database can't digest periods in "
                           "dictionary keys. We have found a number entries"
                           "in your spreadsheet that will violate this."
                           "these are listed below:\n{}\n"
                           "As annoying as this is, we suggest you change "
                           "the sample name to remove the {} characters,"
                           " for example, you could replace {} with {} in "
                           "your spreadsheet."
                           .format(invalid_key_list, invalid_chr,
                                   suggested_chr))
