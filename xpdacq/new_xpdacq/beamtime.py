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
        return os.path.join(glbl.yaml_dir,
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
                    ['{i}: {sp!r}'.format(i=i, sp=sp.short_summary())
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
        #return os.path.join(glbl.yaml_dir, '{pi_name}', 'experiments',
        #                    '{experiment_name}.yml').format(**self)
        return os.path.join(glbl.yaml_dir, 'experiments',
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
        return os.path.join(glbl.yaml_dir, 'samples',
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
        pe1c = glbl.area_det
        # pass parameter to plan_func
        plan = self.plan_func([pe1c], *self['args'], **self['kwargs'])
        return plan

    def short_summary(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = '_'.join([self['plan_name']] + list(arg_value_str))
        return fn

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
        return os.path.join(glbl.yaml_dir, 'scanplans',
                            '%s.yml' % fn)


