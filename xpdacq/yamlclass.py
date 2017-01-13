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
import yaml

class YamlClass:
    """
    special class automatically yamlize user-defined attributes
    if they are updated
    """

    def __init__(self, internal_dict=None):
        # dict stores values of valid attributes
        if internal_dict is None:
            internal_dict = {}
        self._internal_dict = internal_dict
        for key in self.tracked_attributes():
            try:
                val = self.__getattribute__(str(key))
                self._internal_dict.update({key:val})
            except AttributeError:
                print("pass {}".format(key))

    def __setattr__(self, key, val):
        if key in self.tracked_attributes():
            self._internal_dict.update({key: val})
            self.flush()
        super().__setattr__(key, val)

    @property
    def filepath(self):
        """property to store location of local yaml file"""
        return self._filepath

    @filepath.setter
    def filepath(self, fpath):
        """setter to create file if it doesn't exist"""
        self._filepath = fpath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        print("filepath is about to be flushed")
        self.flush()

    def tracked_attributes(self):
        """method to defined attributes that will be serialized"""
        pass

    def flush(self):
        """method to yamlize allowed attributes"""
        with open(self._filepath, 'w') as f:
            yaml.dump(self._internal_dict, f, default_flow_style=False)
