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
import os
import tempfile
import yaml
import abc
from collections import ChainMap


class _YamlDictLike:
    """
    A dict-like wrapper over a YAML file

    Supports the dict-like (MutableMapping) interface plus a `flush` method
    to manually update the file to the state of the dict.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._referenced_by = []  # to be flushed whenever this is flushed
        self.filepath = self.default_yaml_path()

    def default_yaml_path(self):
        return tempfile.NamedTemporaryFile().name

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, fname):
        self._filepath = fname
        # dont create dir if parent doesn't exist yet
        # os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if os.path.isdir(os.path.dirname(self.filepath)):
            self.flush()

    @abc.abstractclassmethod
    def from_yaml(self, f):
        pass

    @abc.abstractmethod
    def to_yaml(self, f=None):
        pass

    def __setitem__(self, key, val):
        res = super().__setitem__(key, val)
        self.flush()
        return res

    def __delitem__(self, key):
        res = super().__delitem__(key)
        self.flush()
        return res

    def clear(self):
        res = super().clear()
        self.flush()
        return res

    def copy(self):
        raise NotImplementedError

    def pop(self, key):
        res = super().pop(key)
        self.flush()
        return res

    def popitem(self):
        res = super().popitem()
        self.flush()
        return res

    def update(self, *args, **kwargs):
        res = super().update(*args, **kwargs)
        self.flush()
        return res

    def setdefault(self, key, val):
        res = super().setdefault(key, val)
        self.flush()
        return res

    def flush(self):
        """
        Ensure any mutable values are updated on disk.
        """
        with open(self.filepath, "w") as f:
            self.to_yaml(f)
        for ref in self._referenced_by:
            ref.flush()


class YamlDict(_YamlDictLike, dict):
    def to_yaml(self, f=None):
        return yaml.dump(dict(self), f, default_flow_style=False)

    @classmethod
    def from_yaml(cls, f):
        d = yaml.load(f)
        # If file is empty, make it an empty dict.
        if d is None:
            d = {}
        elif not isinstance(d, dict):
            raise TypeError(
                "yamldict only applies to YAML files with a " "mapping"
            )
        instance = cls(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance


class YamlChainMap(_YamlDictLike, ChainMap):
    def to_yaml(self, f=None):
        return yaml.dump(
            list(map(dict, self.maps)), f, default_flow_style=False
        )

    @classmethod
    def from_yaml(cls, f):
        maps = yaml.load(f)
        # If file is empty, make it an empty list.
        if maps is None:
            maps = []
        elif not isinstance(maps, list):
            raise TypeError(
                "yamlchainmap only applies to YAML files with "
                "list of mappings"
            )
        instance = cls(*maps)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance
