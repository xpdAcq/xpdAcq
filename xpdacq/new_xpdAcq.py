import uuid
import time
from mock import MagicMock
from collections import ChainMap
import bluesky.plans as bp
import numpy as np
from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.callbacks import LiveTable
#from bluesky.callbacks.broker import verify_files_saved
from xpdacq.beamtime import ScanPlan
from xpdacq.beamtime import Sample
from xpdacq.glbl import glbl


import yaml
import inspect
from .yamldict import YamlDict, YamlChainMap
from xpdacq.validated_dict import ValidatedDictLike

verify_files_saved = MagicMock()


# This is used to map plan names (strings in the YAML file) to actual
# plan functions in Python.
_PLAN_REGISTRY = {}


def register_plan(plan_name, plan_func, overwrite=False):
    if plan_name in _PLAN_REGISTRY and not overwrite:
        raise KeyError("A plan is already registered by this name. Use "
                       "overwrite=True to overwrite it.")
    _PLAN_REGISTRY[plan_name] = plan_func


def unregister_plan(plan_name):
    del _PLAN_REGISTRY[plan_name]


def _summarize(plan):
    "based on bluesky.utils.print_summary"
    output = []
    read_cache = []
    for msg in plan:
        cmd = msg.command
        if cmd == 'open_run':
            output.append('{:=^80}'.format(' Open Run '))
        elif cmd == 'close_run':
            output.append('{:=^80}'.format(' Close Run '))
        elif cmd == 'set':
            output.append('{motor.name} -> {args[0]}'.format(motor=msg.obj,
                                                             args=msg.args))
        elif cmd == 'create':
            pass
        elif cmd == 'read':
            read_cache.append(msg.obj.name)
        elif cmd == 'save':
            output.append('  Read {}'.format(read_cache))
            read_cache = []
    return '\n'.join(output)


def use_photon_shutter():
    glbl.shutter = 'foo'


def use_fast_shutter():
    glbl.shutter = 'fastfoo'


class CustomizedRunEngine(RunEngine):
    def __call__(self, sample, plan, subs=None, *, raise_if_interrupted=False
            , verify_write=False, auto_dark=True, dk_window=3000,**metadata_kw):
        _subs = normalize_subs_input(subs)
        # For simple usage, allow sample to be a plain dict or a Sample.
        if isinstance(sample, Sample):
            sample_md = sample.md
        else:
            sample_md = sample
        #if livetable:
        #    _subs.update({'all':LiveTable([pe1c, temp_controller])})
        if verify_write:
            _subs.update({'stop':verify_files_saved})
        # No keys in metadata_kw are allows to collide with sample keys.
        if set(sample_md) & set(metadata_kw):
            raise ValueError("These keys in metadata_kw are illegal "
                             "because they are always in sample: "
                             "{}".format(set(sample_md) & set(metadata_kw)))
        metadata_kw.update(sample_md)
        if isinstance(plan, ScanPlan):
            plan = plan.factory()
        sh = glbl.shutter
        # force to open shutter before scan and close it after
        plan = bp.pchain(bp.abs_set(sh, 1), plan, bp.abs_set(sh, 0))
        super().__call__(plan, subs,
                         raise_if_interrupted=raise_if_interrupted,
                         **metadata_kw)


def ct(dets, exposure, *, md=None):
    pe1c, = dets
    if md is None:
        md = {}
    # setting up detector
    pe1c.number_of_sets.put(1)
    pe1c.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = pe1c.cam.acquire_time.get()
    # compute number of frames and save metadata
    num_frame = np.ceil(exposure / acq_time)
    if num_frame == 0:
        num_frame = 1
    computed_exposure = num_frame*acq_time
    pe1c.images_per_set.put(num_frame)
    print("INFO: requested exposure time = {} - > computed exposure time"
          "= {}".format(exposure, computed_exposure))
    _md = ChainMap(md, {'sp_time_per_frame': acq_time,
                        'sp_num_frames': num_frame,
                        'sp_requested_exposure': exposure,
                        'sp_computed_exposure': computed_exposure,
                        'sp_type': 'ct',
                        # need a name that shows all parameters values
                        # 'sp_name': 'ct_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'plan_name': 'ct'})
    plan = bp.count([pe1c], md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([pe1c]))
    yield from plan


def new_short_uid():
    return str(uuid.uuid4())[:8]


class Beamtime(ValidatedDictLike, YamlDict):
    _REQUIRED_FIELDS = ['pi_name', 'safnum']

    def __init__(self, pi_name, safnum, **kwargs):
        super().__init__(pi_name=pi_name, safnum=safnum, **kwargs)
        self.setdefault('beamtime_uid', new_short_uid())

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields {}".format(missing))

    def default_yaml_path(self):
        return '{pi_name}.yml'.format(**self)

    def register_experiment(self, experiment):
        self._referenced_by.append(experiment)


class Experiment(ValidatedDictLike, YamlChainMap):
    _REQUIRED_FIELDS = ['experiment_name']

    def __init__(self, experiment_name, beamtime, **kwargs):
        experiment = dict(experiment_name=experiment_name, **kwargs)
        super().__init__(experiment, beamtime)
        self.beamtime = beamtime
        self.setdefault('experiment_uid', new_short_uid())
        beamtime.register_experiment(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields {}".format(missing))

    def default_yaml_path(self):
        return '{experiment_name}.yml'.format(**self)

    def register_sample(self, sample):
        self._referenced_by.append(sample)


class Sample(ValidatedDictLike, YamlChainMap):
    _REQUIRED_FIELDS = ['name', 'composition']

    def __init__(self, name, experiment, *, composition, **kwargs):
        experiment.register_sample(self)
        sample = dict(name=name, composition=composition, **kwargs)
        super().__init__(sample, experiment)
        self.experiment = experiment
        self.setdefault('sample_uid', new_short_uid())

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields {}".format(missing))

    def default_yaml_path(self):
        return '{name}.yml'.format(**self)


class ScanPlan:
    def __init__(self, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        self.plan_name = plan_func.__name__
        self.args = args
        self.kwargs = kwargs
        self.to_yaml(self.default_yaml_path())

    @property
    def bound_arguments(self):
        signature = inspect.signature(self.plan_func)
        # empty list is for [pe1c]  
        bound_arguments = signature.bind([], *self.args, **self.kwargs)
        bound_arguments.apply_defaults()
        complete_kwargs = bound_arguments.arguments
        # remove place holder for [pe1c]
        complete_kwargs.popitem(False)
        return complete_kwargs

    def factory(self):
        # grab the area detector used in current configuration
        pe1c = glbl.pe1c
        # pass parameter to plan_func
        plan = self.plan_func([pe1c], *self.args, **self.kwargs)
        return plan

    def __str__(self):
        return _summarize(self.factory())

    def __eq__(self, other):
        return self.to_yaml() == other.to_yaml()

    def to_yaml(self, fname=None):
        "With yaml.dump, return a string if fname is None"
        # Get the complete arguments to plan_func as a dict.
        # Even args that were given is positional will be mapped to
        # their name.
        yaml_info = {}
        yaml_info['plan_args'] = dict(self.bound_arguments)
        yaml_info['plan_name'] = self.plan_name
        if fname is None:
            return yaml.dump(yaml_info)
        else:
            with open(fname, 'w') as f:
                yaml.dump(yaml_info, f)  # returns None

    def default_yaml_path(self):
        arg_value_str = map(str, self.bound_arguments.values())
        return '_'.join([self.plan_name] + list(arg_value_str))

    @classmethod
    def from_yaml(cls, f):
        d = yaml.load(f)
        plan_name = d['plan_name']  # i.e., 'ct'
        plan_args = d['plan_args']  # i.e., {'exposure': 1}
        plan_func = _PLAN_REGISTRY[plan_name]
        return cls(plan_func, **plan_args)


register_plan('ct', ct)
