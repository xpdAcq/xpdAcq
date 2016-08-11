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

from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .validated_dict import ValidatedDictLike


# This is used to map plan names (strings in the YAML file) to actual
# plan functions in Python.
_PLAN_REGISTRY = {}

def register_plan(plan_name, plan_func, overwrite=False):
    "Map between a plan_name (string) and a plan_func (generator function)."
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


def _configure_pe1c(exposure):
    """ priviate function to configure pe1c with continuous acquistion
    mode"""
    #acq_time = glbl.area_det.cam.acquire_time.get()
    #cs studio configuration doesn't propagate to python level
    acq_time = glbl.area_det.cam.acquire_time.put(glbl.frame_acq_time)
    # compute number of frames
    num_frame = np.ceil(exposure / acq_time)
    if num_frame == 0:
        num_frame = 1
    computed_exposure = num_frame*acq_time
    glbl.area_det.images_per_set.put(num_frame)
    # print exposure time
    print("INFO: requested exposure time = {} - > computed exposure time"
          "= {}".format(exposure, computed_exposure))
    return (num_frame, acq_time, computed_exposure)


def ct(dets, exposure, *, md=None):
    pe1c, = dets
    if md is None:
        md = {}
    # setting up area_detector
    (num_frame, acq_time, computed_exposure) = _configure_pe1c(exposure)
    # update md
    _md = ChainMap(md, {'sp_time_per_frame': acq_time,
                        'sp_num_frames': num_frame,
                        'sp_requested_exposure': exposure,
                        'sp_computed_exposure': computed_exposure,
                        'sp_type': 'ct',
                        # need a name that shows all parameters values
                        #'sp_name': 'ct_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'sp_plan_name': 'ct'})
    plan = bp.count([glbl.area_det], md = _md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det]))
    yield from plan

def Tramp(dets, exposure, Tstart, Tstop, Tstep, *, md=None):
    pe1c, = dets
    if md is None:
        md = {}
    # setting up area_detector
    (num_frame, acq_time, computed_exposure) = _configure_pe1c(exposure)
    # compute Nsteps
    (Nsteps, computed_step_size) = _nstep(Tstart, Tstop, Tstep)
    # update md
    _md = ChainMap(md, {'sp_time_per_frame': acq_time,
                        'sp_num_frames': num_frame,
                        'sp_requested_exposure': exposure,
                        'sp_computed_exposure': computed_exposure,
                        'sp_type': 'Tramp',
                        'sp_startingT': Tstart,
                        'sp_endingT': Tstop,
                        'sp_requested_Tstep': Tstep,
                        'sp_computed_Tstep': computed_step_size,
                        'sp_Nsteps': Nsteps,
                        # need a name that shows all parameters values
                        #'sp_name': 'Tramp_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'sp_plan_name': 'Tramp'})
    plan = bp.scan([glbl.area_det], glbl.temp_controller, Tstart, Tstop, Nsteps, md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det, glbl.temp_controller]))
    yield from plan

def tseries(dets, exposure, delay, num, *, md = None):
    pe1c, = dets
    if md is None:
        md = {}
    # setting up area_detector
    (num_frame, acq_time, computed_exposure) = _configure_pe1c(exposure)
    real_delay = max(0, delay - computed_exposure)
    period = max(computed_exposure, real_delay + computed_exposure)
    print('INFO: requested delay = {}s  -> computed delay = {}s'
          .format(delay, real_delay))
    print('INFO: nominal period (neglecting readout overheads) of {} s'
          .format(period))
    # update md
    _md = ChainMap(md, {'sp_time_per_frame': acq_time,
                        'sp_num_frames': num_frame,
                        'sp_requested_exposure': exposure,
                        'sp_computed_exposure': computed_exposure,
                        'sp_type': 'tseries',
                        # need a name that shows all parameters values
                        # 'sp_name': 'tseries_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'sp_plan_name': 'tseries'})
    plan = bp.count([glbl.area_det], num, delay, md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det]))
    yield from plan

def _nstep(start, stop, step_size):
    ''' return (start, stop, nsteps)'''
    requested_nsteps = abs((start - stop) / step_size)

    computed_nsteps = int(requested_nsteps)+1 # round down for finer step size
    computed_step_list = np.linspace(start, stop, computed_nsteps)
    computed_step_size = computed_step_list[1]- computed_step_list[0]
    print("INFO: requested temperature step size = {} ->"
          "computed temperature step size = {}"
          .format(step_size,computed_step_size))
    return (computed_nsteps, computed_step_size)


register_plan('ct', ct)
register_plan('Tramp', Tramp)
register_plan('tseries', tseries)


def new_short_uid():
    return str(uuid.uuid4())[:8]


def _clean_info(obj):
    """ stringtify and replace space"""
    return str(obj).strip().replace(' ', '_')


class Beamtime(ValidatedDictLike, YamlDict):
    #_REQUIRED_FIELDS = ['pi', 'saf_num']
    _REQUIRED_FIELDS = ['bt_piLast', 'bt_safN']

    def __init__(self, pi_last, saf_num, experimenters=[], *,
                 wavelength=None, **kwargs):
        super().__init__(bt_piLast=_clean_info(pi_last),
                         bt_safN=_clean_info(saf_num),
                         bt_experimenters=experimenters,
                         bt_wavelength=wavelength, **kwargs)
        self._wavelength = wavelength
        #self.experiments = []
        self.scanplans = []
        self.samples = []
        self._referenced_by = []
        # used by YamlDict
        self.setdefault('bt_uid', new_short_uid())

    @property
    def wavelength(self):
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val):
        self._wavelength = val
        self.update(bt_wavelength=val)


    def register_scanplan(self, scanplan):
        self.scanplans.append(scanplan)
        self._referenced_by.extend([el for el in self.scanplans if el
                                    not in self._referenced_by])

    @property
    def md(self):
        return dict(self)

    def validate(self):
        # This is automatically called whenever the contents are changed.
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.yaml_dir,
                            'bt_bt.yml').format(**self)

    def register_sample(self, sample):
        # Notify this Beamtime about an Sample that should be re-synced
        # whenever the contents of the Beamtime are edited. 
        self.samples.append(sample)
        self._referenced_by.extend([el for el in self.samples if el
                                    not in self._referenced_by])

    @classmethod
    def from_yaml(cls, f):
        d = yaml.load(f)
        instance = cls.from_dict(d)
        if not isinstance(f, str):
            instance.filepath = os.path.abspath(f.name)
        return instance

    @classmethod
    def from_dict(cls, d):
        return cls(d.pop('bt_piLast'),
                   d.pop('bt_safN'),
                   d.pop('bt_experimenters'),
                   wavelength=d.pop('bt_wavelength'),
                   bt_uid=d.pop('bt_uid'),
                   **d)

    def __str__(self):
        contents = (['', 'ScanPlans:'] +
                    ['{i}: {sp!r}'.format(i=i, sp=sp.short_summary())
                     for i, sp in enumerate(self.scanplans)] +
                    ['', 'Samples:'] +
                    ['{i}: {sa_name}'.format(i=i, **s)
                     for i, s in enumerate(self.samples)])
        return '\n'.join(contents)

    def list(self):
        # for back-compat
        print(self)


#class Sample(ValidatedDictLike, YamlDict):
class Sample(ValidatedDictLike, YamlChainMap):
    _REQUIRED_FIELDS = ['sa_name', 'sa_composition']

    def __init__(self, beamtime, sample_md, *, composition=None, **kwargs):
        composition = sample_md['sa_composition']
        if not isinstance(composition, dict) or not composition:
            print("WARNING: for the richeness of your"
                  "metadata, please enter your sample "
                  "composition information as a dictionary "
                  "with elements and quantities. For example: "
                  "{'Ni':1}, {'Ti':1, 'O':2}")
        super().__init__(sample_md, beamtime)
        self.beamtime = beamtime
        self.setdefault('sa_uid', new_short_uid())
        beamtime.register_sample(self)

    @property
    def md(self):
        return dict(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.yaml_dir, 'samples',
                            '{sa_name}.yml').format(**self)

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
        composition = map1.pop('sa_composition')
        return cls(map1, beamtime,
                   sa_uid=map1.pop('sa_uid'),
                   composition=composition,
                   **map1)

#class ScanPlan(ValidatedDictLike, YamlDict):
class ScanPlan(ValidatedDictLike, YamlChainMap):
    def __init__(self, beamtime, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        plan_name = plan_func.__name__
        sp_dict = {'sp_plan_name': plan_name , 'sp_args': args,
                   'sp_kwargs': kwargs}
        if 'sp_uid' in sp_dict['sp_kwargs']:
            scanplan_uid = sp_dict['sp_kwargs'].pop('sp_uid')
            sp_dict.update({'sp_uid':scanplan_uid})
        super().__init__(sp_dict, beamtime)
        #super().__init__(sp_dict)
        self.setdefault('sp_uid', new_short_uid())
        beamtime.register_scanplan(self)

    @property
    def md(self):
        open_run, = [msg for msg in self.factory() if
                     msg.command == 'open_run']
        return open_run.kwargs

    @property
    def bound_arguments(self):
        signature = inspect.signature(self.plan_func)
        # empty list is for [pe1c]  
        bound_arguments = signature.bind([], *self['sp_args'],
                                         **self['sp_kwargs'])
        #bound_arguments.apply_defaults() # only valid in py 3.5
        complete_kwargs = bound_arguments.arguments
        # remove place holder for [pe1c]
        complete_kwargs.popitem(False)
        return complete_kwargs

    def factory(self):
        # grab the area detector used in current configuration
        pe1c = glbl.area_det
        # pass parameter to plan_func
        plan = self.plan_func([pe1c], *self['sp_args'], **self['sp_kwargs'])
        return plan

    def short_summary(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = '_'.join([self['sp_plan_name']] + list(arg_value_str))
        return fn

    def __str__(self):
        return _summarize(self.factory())

    def __eq__(self, other):
        return self.to_yaml() == other.to_yaml()

#    @classmethod
#    def from_yaml(cls, f):
#        d = yaml.load(f)
#        instance = cls.from_dict(d)
#        if not isinstance(f, str):
#            instance.filepath = os.path.abspath(f.name)
#        return instance

#    @classmethod
#    def from_dict(cls, d):
#        plan_name = d.pop('sp_plan_name')
#        plan_func = _PLAN_REGISTRY[plan_name]
#        plan_uid = d.pop('sp_uid')
#        sp_args = d['sp_args']
#        sp_kwargs = d['sp_kwargs']
#        sp_kwargs.update({'sp_uid':plan_uid})
#        return cls(plan_func,
#                   *d['sp_args'],
#                   **sp_kwargs)

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
        plan_name = map1.pop('sp_plan_name')
        plan_func = _PLAN_REGISTRY[plan_name]
        plan_uid = map1.pop('sp_uid')
        sp_args = map1['sp_args']
        sp_kwargs = map1['sp_kwargs']
        sp_kwargs.update({'sp_uid':plan_uid})
        return cls(beamtime, plan_func, **map1)

#    @classmethod
#    def from_yaml(cls, f, experiment=None, beamtime=None):
#        map1, map2, map3 = yaml.load(f)
#        instance = cls.from_dicts(map1, map2, map3, experiment, beamtime)
#        if not isinstance(f, str):
#            instance.filepath = os.path.abspath(f.name)
#        return instance

#    @classmethod
#    def from_dicts(cls, map1, map2, map3, experiment=None, beamtime=None):
#        if experiment is None:
#            experiment = Experiment.from_dicts(map2, map3, beamtime=beamtime)
#        plan_name = map1.pop('sp_plan_name')
#        plan_func = _PLAN_REGISTRY[plan_name]
#        plan_uid = map1.pop('sp_uid')
#        sp_kwargs = map1['sp_kwargs']
#        sp_kwargs.update({'sp_uid':plan_uid})
#        return cls(experiment, plan_func,
#                   *map1['sp_args'],
#                   **sp_kwargs)

    def default_yaml_path(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = '_'.join([self['sp_plan_name']] + list(arg_value_str))
        return os.path.join(glbl.yaml_dir, 'scanplans',
                            '%s.yml' % fn)

