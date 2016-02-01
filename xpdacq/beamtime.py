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
class Beamtime(object):
    def __init__(self,):


    @property
    def B_DIR(self):
        # FIXME: confirm where to put backup dir
        return os.path.expanduser('~/xpdBackup') # remote backup directory
