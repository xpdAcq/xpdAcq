# ######################################################################
# Copyright (c) 2016, Brookhaven Science Associates, Brookhaven        #
# National Laboratory. All rights reserved.                            #
#                                                                      #
# BSD 3-Clause                                                         #
# ######################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import tempfile
import yaml
import os


class YamlDict(dict):
    """
    A dict-like wrapper over a YAML file

    Supports the dict-like (MutableMapping) interface plus a `flush` method
    to manually update the file to the state of the dict.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We need *some* file to back the YAMLDict. Until the user or
        # subclass gives us a filepath, just make one in /tmp.
        self._referenced_by = []  # other YAMLDicts to be flushed when this is
        self.filepath = self.default_yaml_path()

    def default_yaml_path(self):
        return tempfile.NamedTemporaryFile().name

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, fname):
        self._filepath = fname
        self.flush()

    @classmethod
    def from_yaml(self, f):
        d = yaml.load(f)
        # If file is empty, make it an empty dict.
        if d is None:
            d = {}
        elif not isinstance(d, dict):
            raise TypeError("yamldict only applies to YAML files with a "
                            "mapping")
        instance = YamlDict(d)
        instance.filepath = f.name  # filepath for current dir
        return instance

    def to_yaml(self, f=None):
        # if f is None, we get back a string. Good for debugging
        return yaml.dump({k: v for k, v in self.items()}, f)

    def __setitem__(self, key, val):
        super().__setitem__(key, val)
        self.flush()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.flush()

    def clear(self):
        super().clear()
        self.flush()

    def copy(self):
        raise NotImplementedError()

    def pop(self, key):
        super().pop(key)
        self.flush()

    def popitem(self):
        super().popitem()
        self.flush()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.flush()

    def setdefault(self, key, val):
        super().setdefault(key, val)
        self.flush()

    def flush(self):
        """
        Ensure any mutable values are updated on disk.
        """
        with open(self.filepath, 'w') as f:
            self.to_yaml(f)
        for ref in self._referenced_by:
            ref.flush()
