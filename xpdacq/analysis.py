#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
#from dataportal import DataBroker as db
#from dataportal import get_events, get_table, get_images
#from metadatastore.commands import find_run_starts
from xpdacq.control import _get_obj

bt = _get_obj('bt')

def bt_uid():
    return bt.get(0).md['bt_uid']
