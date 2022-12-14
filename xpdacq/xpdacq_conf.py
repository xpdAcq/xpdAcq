"""main module of configuring xpdacq"""
# !/usr/bin/env python
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
import contextlib
import datetime
import os
import platform
import pprint
import subprocess
import time
import warnings

import yaml
from xpdconf.conf import glbl_dict, GLBL_YAML_PATH

from .tools import xpdAcqException
from .yamldict import YamlDict

glbl_dict.pop("exp_db")
XPDACQ_MD_VERSION = 0.1

# special function and dict to store all necessary objects
xpd_configuration = {}


def configure_device(*, area_det, shutter, temp_controller, db, **kwargs):
    """function to set up required device/objects for xpdacq"""
    # specifically assign minimum requirements
    xpd_configuration["area_det"] = area_det
    xpd_configuration["shutter"] = shutter
    xpd_configuration["temp_controller"] = temp_controller
    xpd_configuration["db"] = db
    # extra kwargs
    xpd_configuration.update(**kwargs)


def configure_frame_acq_time(new_frame_acq_time):
    """function to configure frame acquire time of area detector"""
    area_det = xpd_configuration["area_det"]
    # stop acquisition
    area_det.cam.acquire.put(0)
    time.sleep(1)
    if hasattr(area_det, 'number_of_sets'):
        area_det.number_of_sets.put(1)
    area_det.cam.acquire_time.put(new_frame_acq_time)
    # extra wait time for device to set
    time.sleep(1)
    area_det.cam.acquire.put(1)
    print(
        "INFO: area detector has been configured to new "
        "acquisition time (time per frame)  = {}s".format(new_frame_acq_time)
    )


def _set_first_max_age(val: float):
    if "xrun" not in xpd_configuration:
        raise xpdAcqException("'xrun' not registered in the xpd_configuration.")
    xpd_configuration["xrun"].dark_preprocessors[0].max_age = val * 60.0
    return


def _verify_within_test(beamline_config_fp, verif):
    while verif != "y":
        with open(beamline_config_fp, "r") as f:
            beamline_config = yaml.unsafe_load(f)
        warnings.warn("Not verified")
        verif = "y"
    beamline_config["Verified by"] = "AUTO VERIFIED IN TEST"
    timestamp = datetime.datetime.now()
    beamline_config["Verification time"] = timestamp.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    with open(beamline_config_fp, "w") as f:
        yaml.dump(beamline_config, f)
    return beamline_config


def _load_beamline_config(beamline_config_fp, verif="", test=False):
    if (not test) and (not os.path.isfile(beamline_config_fp)):
        raise xpdAcqException(
            "WARNING: can not find long term beamline "
            "configuration file. Please contact the "
            "beamline scientist ASAP"
        )
    pp = pprint.PrettyPrinter()
    os_type = platform.system()
    if os_type == "Windows":
        editor = "notepad"
    else:
        editor = os.environ.get("EDITOR", "vim")
    beamline_config = dict()
    if not test:
        while verif.upper() != ("Y" or "YES"):
            with open(beamline_config_fp, "r") as f:
                beamline_config = yaml.unsafe_load(f)
            pp.pprint(beamline_config)
            verif = input("\nIs this configuration correct? y/n: ")
            if verif.upper() == ("N" or "NO"):
                print("Edit, save, and close the configuration file.\n")
                subprocess.call([editor, beamline_config_fp])
        beamline_config["Verified by"] = input("Please input your initials: ")
        timestamp = datetime.datetime.now()
        beamline_config["Verification time"] = timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        with open(beamline_config_fp, "w") as f:
            yaml.dump(beamline_config, f)
    return beamline_config


def _reload_glbl(glbl_yaml_path=None):
    """function to reload glbl yaml

    Parameters
    ----------
    glbl_yaml_path : str, optional
        filepath to local yaml
    """
    if glbl_yaml_path is None:
        glbl_yaml_path = glbl_dict["glbl_yaml_path"]
    if os.path.isfile(glbl_yaml_path):
        with open(glbl_dict["glbl_yaml_path"]) as f:
            reload_dict = yaml.unsafe_load(f)
        return reload_dict
    else:
        pass


def _set_glbl(glbl_obj, reload_dict):
    """function to set glbl object based on reload contents

    Parameters
    ----------
    glbl_obj : xpdacq.xpdacq_conf.GlblYamlDict
        instance of GlblYamlDict that is going to be updated
    reload_dict : dict
        a dictionary based on reload of glbl yaml
    """
    for k, v in reload_dict.items():
        if k in glbl_obj.mutable_fields:
            glbl_obj[k] = v


class GlblYamlDict(YamlDict):
    """
    class holds global options of xpdAcq.

    It automatically updates the contents of local yaml file when the
    contents of class are changed, and for back-support, it issues a
    Deprecationwarning when user tries to set attributes

    Parameters:
    -----------
    name : str
        name of this object. It's *suggested* to be the same as
        the instance name. i.e. glbl = GlblYamlDict('glbl', **kwargs)
    kwargs :
        keyword arguments for global options
    """

    # required attributes for yaml
    _VALID_ATTRS = ["_name", "_filepath", "filepath", "_referenced_by"]

    # keys for fields allowed to change
    _MUTABLE_FIELDS = [
        "frame_acq_time",
        "auto_dark",
        "dk_window",
        "_dark_dict_list",
        "shutter_control",
        "auto_load_calib",
        "calib_config_name",
        "calib_config_dict",
        "image_field",
        "exp_hash_uid",
        "_active_beamtime"
    ]

    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._referenced_by = []
        self._name = name

    @property
    def mutable_fields(self):
        """keys for fields that are allowed to updated"""
        return self._MUTABLE_FIELDS

    def default_yaml_path(self):
        return GLBL_YAML_PATH

    def __setitem__(self, key, val):
        if key not in self._MUTABLE_FIELDS:
            raise xpdAcqException(
                "key='{}' is not allowed to change!".format(key)
            )
        else:
            super().__setitem__(key, val)

    def __setattr__(self, key, val):
        if key not in self._VALID_ATTRS:
            if key in self._MUTABLE_FIELDS:
                # back-support
                raise DeprecationWarning(
                    "{} has been changed, please do "
                    "this command instead\n"
                    ">>> {}['{}']={}".format(self._name, self._name, key, val)
                )
            else:
                raise AttributeError(
                    "{} doesn't support setting attribute".format(self._name)
                )
        else:
            if key == "frame_acq_time":
                configure_frame_acq_time(val)
            elif key == "dk_window":
                _set_first_max_age(val)
            super().__setattr__(key, val)

    @classmethod
    def from_yaml(cls, f):
        """method to reload object from local yaml"""
        d = yaml.unsafe_load(f)
        instance = cls.from_dict(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dict(cls, d):
        """method to reload object from dict"""
        return cls(**d)

    # From xonsh Copyright 2015-2016, the xonsh developers.
    # All rights reserved.
    @contextlib.contextmanager
    def swap(self, other=None, **kwargs):
        """Provides a context manager for temporarily swapping out certain
        variables with other values. On exit from the context
        manager, the original values are restored.
        """
        old = {}
        # single positional argument should be a dict-like object
        if other is not None:
            for k, v in other.items():
                old[k] = self.get(k, NotImplemented)
                dict.__setitem__(self, k, v)
        # kwargs could also have been sent in
        for k, v in kwargs.items():
            old[k] = self.get(k, NotImplemented)
            dict.__setitem__(self, k, v)

        exception = None
        try:
            yield self
        except Exception as e:
            exception = e
        finally:
            # restore the values
            for k, v in old.items():
                if v is NotImplemented:
                    del self[k]
                else:
                    self[k] = v
            if exception is not None:
                raise exception from None
