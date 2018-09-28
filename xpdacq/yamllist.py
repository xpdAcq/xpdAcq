# ######################################################################
# Copyright (c) 2016, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# BSD 3-Clause                                                         #
# ######################################################################

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
import yaml


class YamlList(list):
    """
    A list-like wrapper over a YAML file

    Supports the list-like interface plus a `flush` method
    to manually update the file to the state of the list. The method is
    automatically called on `__setitem__`, `__del__`, and on Python exit.
    """

    def __init__(self, fname):
        self.fname = fname
        with open(fname, "r") as f:
            lst = yaml.load(f)
        # If file is empty, make it an empty list.
        if lst is None:
            lst = []
        elif not isinstance(lst, list):
            raise TypeError("yamllist only applies to YAML files with a list")
        super().__init__(lst)
        self.flush()

    def __setitem__(self, index, val):
        super().__setitem__(index, val)
        self.flush()

    def __delitem__(self, index):
        super().__delitem__(index)
        self.flush()

    def append(self, val):
        super().append(val)
        self.flush()

    def clear(self):
        super().clear()
        self.flush()

    def copy(self):
        raise NotImplementedError

    def extend(self, val):
        super().extend(val)
        self.flush()

    def insert(self, index, val):
        super().insert(index, val)
        self.flush()

    def pop(self, val=None):
        super().pop(val)
        self.flush()

    def remove(self, val):
        super().remove(val)
        self.flush()

    def reverse(self):
        super().reverse()
        self.flush()

    def sort(self):
        super().sort()
        self.flush()

    def flush(self):
        """
        Ensure any mutable values are updated on disk.
        """
        with open(self.fname, "w") as f:
            yaml.dump(list(self), f)
