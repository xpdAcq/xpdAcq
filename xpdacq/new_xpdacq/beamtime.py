import os
import uuid
import time
import yaml
import inspect
from mock import MagicMock
from collections import ChainMap
import bluesky.plans as bp
import numpy as np
from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.callbacks import LiveTable
#from bluesky.callbacks.broker import verify_files_saved

# FIXME
from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .validated_dict import ValidatedDictLike

def new_short_uid():
    return str(uuid.uuid4())[:8]


class Beamtime(ValidatedDictLike, YamlDict):
    _REQUIRED_FIELDS = ['pi_name', 'safnum']

    def __init__(self, pi_name, safnum, **kwargs):
        super().__init__(pi_name=pi_name, safnum=safnum, **kwargs)
        self.pi_name = pi_name
        self.saf_num = safnum
        self.experiments = []
        self.samples = []
        self._referenced_by = self.experiments  # used by YamlDict
        self.setdefault('beamtime_uid', new_short_uid())

    @property
    def scanplans(self):
        return [s for e in self.experiments for s in e.scanplans]

    def validate(self):
        # This is automatically called whenever the contents are changed.
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.config_base,
                            'bt_bt.yml').format(**self)

    def register_experiment(self, experiment):
        # Notify this Beamtime about an Experiment that should be re-synced
        # whenever the contents of the Beamtime are edited.
        self.experiments.append(experiment)

    @classmethod
    def from_yaml(cls, f):
        d = yaml.load(f)
        instance = cls.from_dict(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dict(cls, d):
        return cls(d.pop('pi_name'),
                   d.pop('safnum'),
                   beamtime_uid=d.pop('beamtime_uid'),
                   **d)

    def __str__(self):
        contents = (['Experiments:'] +
                    ['{i}: {experiment_name}'.format(i=i, **e)
                     for i, e in enumerate(self.experiments)] +
                    ['', 'ScanPlans:'] +
                    ['{i}: {sp!r}'.format(i=i, sp=sp)
                     for i, sp in enumerate(self.scanplans)] +
                    ['', 'Samples:'] +
                    ['{i}: {name}'.format(i=i, **s)
                     for i, s in enumerate(self.samples)])
        return '\n'.join(contents)

    def list(self):
        # for back-compat
        print(self)


class Experiment(ValidatedDictLike, YamlChainMap):
    _REQUIRED_FIELDS = ['experiment_name']

    def __init__(self, experiment_name, beamtime, **kwargs):
        experiment = dict(experiment_name=experiment_name, **kwargs)
        super().__init__(experiment, beamtime)
        self.beamtime = beamtime
        self.scanplans = []
        self._referenced_by = self.scanplans # used by YamlDict
        self.setdefault('experiment_uid', new_short_uid())
        beamtime.register_experiment(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.xpdconfig, '{pi_name}', 'experiments',
                            '{experiment_name}.yml').format(**self)

    def register_scanplan(self, scanplan):
        # Notify this Experiment about a ScanPlan that should be re-synced
        # whenever the contents of the Experiment are edited.
        self.scanplans.append(scanplan)

    @classmethod

    def from_yaml(cls, f, beamtime=None):
        map1, map2 = yaml.load(f)
        instance = cls.from_dicts(map1, map2, beamtime=beamtime)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dicts(cls, map1, map2, beamtime=None):
        if beamtime is None:
            beamtime = Beamtime.from_dict(map2)
        return cls(map1.pop('experiment_name'), beamtime,
                   experiment_uid=map1.pop('experiment_uid'),
                   **map1)


class Sample(ValidatedDictLike, YamlDict):
    _REQUIRED_FIELDS = ['name', 'composition']

    def __init__(self, name, *, composition, **kwargs):
        sample = dict(name=name, composition=composition, **kwargs)
        super().__init__(sample)
        self.setdefault('sample_uid', new_short_uid())

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.xpdconfig, 'samples',
                            '{name}.yml').format(**self)


class ScanPlan(ValidatedDictLike, YamlChainMap):
    def __init__(self, experiment, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        self.experiment = experiment
        experiment.register_scanplan(self)
        plan_name = plan_func.__name__
        super().__init__({'plan_name': plan_name , 'args': args,
                          'kwargs': kwargs}, *experiment.maps)
        self.setdefault('scanplan_uid', new_short_uid())

    @property
    def bound_arguments(self):
        signature = inspect.signature(self.plan_func)
        # empty list is for [pe1c]  
        bound_arguments = signature.bind([], *self['args'], **self['kwargs'])
        bound_arguments.apply_defaults()
        complete_kwargs = bound_arguments.arguments
        # remove place holder for [pe1c]
        complete_kwargs.popitem(False)
        return complete_kwargs

    def factory(self):
        # grab the area detector used in current configuration
        pe1c = glbl.pe1c
        # pass parameter to plan_func
        plan = self.plan_func([pe1c], *self['args'], **self['kwargs'])
        return plan

    def __str__(self):
        return _summarize(self.factory())

    def __eq__(self, other):
        return self.to_yaml() == other.to_yaml()

    @classmethod
    def from_yaml(cls, f, experiment=None, beamtime=None):
        map1, map2, map3 = yaml.load(f)
        instance = cls.from_dicts(map1, map2, map3, experiment, beamtime)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dicts(cls, map1, map2, map3, experiment=None, beamtime=None):
        if experiment is None:
            experiment = Experiment.from_dicts(map2, map3, beamtime=beamtime)
        plan_name = map1.pop('plan_name')
        plan_func = _PLAN_REGISTRY[plan_name]
        return cls(experiment, plan_func,
                   *map1['args'], **map1['kwargs'])

    def default_yaml_path(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = '_'.join([self['plan_name']] + list(arg_value_str))
        return os.path.join(glbl.xpdconfig, '{pi_name}', 'scanplans',
                            '%s.yml' % fn).format(**self)


def load_beamtime(directory):
    """
    Load a Beamtime and associated objects.

    Expected directory structure:

    <glbl.xpdconfig>/
      samples/
      <pi_name1>/
        beamtime.yml
        scanplans/
        experiments/
      <pi_name2>/
        beamtime.yaml
        scanplans/
        experiments
    """
    known_uids = {}
    beamtime_fn = os.path.join(directory, 'beamtime.yml')
    experiment_fns = os.listdir(os.path.join(directory, 'experiments'))
    sample_fns = os.listdir(os.path.join(directory, '..', 'samples'))
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
        with open(os.path.join(directory, '..', 'samples', fn), 'r') as f:
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


