# ######################################################################
# Copyright (c) 2016, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# BSD 3-Clause                                                         #
# ######################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import yaml
from collections import MutableMapping


class YamlDict(MutableMapping):
    """
    A dict-like wrapper over a YAML file

    Supports the dict-like (MutableMapping) interface plus a `flush` method
    to manually update the file to the state of the dict. The method is
    automatically called on `__setitem__`, `__del__`, and on Python exit.
    """
    def __init__(self, fname):
        self.fname = fname
        with open(fname, 'r') as f:
            d = yaml.load(f)
        print(d)
        print(type(d))
        # If file is empty, make it an empty dict.
        if d is None:
            d = {}
        elif not isinstance(d, dict):
            raise TypeError("yamldict only applies to YAML files with a "
                            "mapping")
        self._cache = d
        self.flush()

    def __repr__(self):
        return repr(dict(self))

    def __getitem__(self, key):
        return self._cache[key]

    def __setitem__(self, key, val):
        self._cache[key] = val
        self.flush()

    def __iter__(self):
        return iter(self._cache)

    def __contains__(self, k):
        return k in self._cache

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        del self._cache[key]
        self.flush()

    def __len__(self):
        return len(self._cache)

    def clear(self):
        self._cache.clear()
        self.flush()

    def flush(self):
        """
        Ensure any mutable values are updated on disk.
        """
        with open(self.fname, 'w') as f:
            yaml.dump(self._cache, f)
