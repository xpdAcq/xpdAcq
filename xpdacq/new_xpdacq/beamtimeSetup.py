import os
import uuid
import time
import yaml
import inspect
from mock import MagicMock
from collections import ChainMap
import bluesky.plans as bp
import numpy as np

from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .validated_dict import ValidatedDictLike
from .beamtime import Beamtime, Experiment, ScanPlan, Sample 

def _start_beamtime(PI_last, saf_num):
    try:
        dir_list = os.path.listdir(glbl.home)
    except FileNotFoundError:
        print("WARNING: fundamental directory {} does not exist"
              "Please contact beamline staff immediately"
              .format(glbl.home))
        return
    if len(dir_list) != 0:
        print("WARNING: There are more than one directories under"
              "{}, did you already run _end_beamtime()"
              .format(glbl.home))

    elif len(dir_list) == 0:
        for el in glbl.allfolders:
            os.makedirs(el, exist_ok=True)
        bt = Beamtime(PI_last, saf_num)
        return bt

def start_xpdacq():
    os.makedirs(glbl.yaml_dir, exist_ok=True)
    bt_list = [f for f in os.listdir(glbl.yaml_dir) if
               f.startswith('bt') and
               os.path.isfile(os.path.join(glbl.yaml_dir, f))]

    if len(bt_list) == 1:
        bt_f = bt_list[-1]
        bt = load_beamtime()
        return bt

    elif len(bt_list) > 1:
        print("WARNING: There are more than one beamtime objects:"
              "{}".format(bt_list))
        print("Please contact beamline staff immediately")

    else:
        print("INFO: No beamtime object has been found")
        print("INFO: Please run _start_beamtime(<PI_last>, <saf_num>)"
              "to initiate beamtime")

def load_beamtime(directory=None):
    """
    Load a Beamtime and associated objects.

    Expected directory structure:

    <glbl.yaml_dir>/
      beamtime.yml
      samples/
      scanplans/
      experiments/
    """
    if directory is None:
        directory = glbl.yaml_dir # leave room for future multi-beamtime
    known_uids = {}
    beamtime_fn = os.path.join(directory, 'bt_bt.yml')
    experiment_fns = os.listdir(os.path.join(directory, 'experiments'))
    sample_fns = os.listdir(os.path.join(directory, 'samples'))
    scanplan_fns = os.listdir(os.path.join(directory, 'scanplans'))

    with open(beamtime_fn, 'r') as f:
        bt = load_yaml(f, known_uids)

    for fn in experiment_fns:
        with open(os.path.join(directory, 'experiments', fn), 'r') as f:
            load_yaml(f, known_uids)

    for fn in scanplan_fns:
        with open(os.path.join(directory, 'scanplans', fn), 'r') as f:
            load_yaml(f, known_uids)

    # Samples are not part of the heirarchy, but all beamtimes know about
    # all Samples.
    for fn in sample_fns:
        with open(os.path.join(directory, 'samples', fn), 'r') as f:
            data = yaml.load(f)
            bt.samples.append(data)

    return bt


def load_yaml(f, known_uids=None):
    """
    Recreate a ScanPlan, Experiment, or Beamtime object from a YAML file.

    If its linked objects have already been created, re-link to them.
    If they have not yet been created, create them now.
    """
    if known_uids is None:
        known_uids = {}
    data = yaml.load(f)
    # If f is a file handle, 'rewind' it so we can read it again.
    if not isinstance(f, str):
        f.seek(0)
    if isinstance(data, dict) and 'beamtime_uid' in data:
        obj = Beamtime.from_yaml(f)
        known_uids[obj['beamtime_uid']] = obj
        return obj
    elif isinstance(data, list) and len(data) == 2:
        beamtime = known_uids.get(data[1]['beamtime_uid'])
        obj = Experiment.from_yaml(f, beamtime=beamtime)
        known_uids[obj['experiment_uid']] = obj
    elif isinstance(data, list) and len(data) == 3:
        experiment = known_uids.get(data[1]['experiment_uid'])
        beamtime = known_uids.get(data[2]['beamtime_uid'])
        obj = ScanPlan.from_yaml(f, experiment=experiment, beamtime=beamtime)
        known_uids[obj['scanplan_uid']] = obj
    else:
        raise ValueError("File does not match a recognized specification.")
    return obj


""" hodding place
# advanced version, allowed multiple beamtime. but not used for now
def _start_xpdacq():
    dirs = [d for d in os.listdir(glbl.yaml_dir) if os.path.isdir(d)]
    # create sample dir if it doesn't exist yet
    if 'samples' not in dirs:
        sample_dir = os.path.join(glbl.xpdconfig, 'samples')
        os.makedirs(sample_dir, exist_ok=True)
    else:
        dirs.remove('samples')
    # now we have all dirs that are not samples;
    # only PI_name dirs left

    if len(dirs) == 1:
        load_dirs = dirs[-1]
        bt = load_beamtime(load_dirs)

    elif len(dirs) > 1:
        print("INFO: There are more than one PI_name dirs:"
              "{}".format(dirs))
        print("Please choose the one you want to use and run:"
              "bt = load_beamtime(<path to the PI name dir>)")

    else:
        print("INFO: No PI_name has been found")

"""
