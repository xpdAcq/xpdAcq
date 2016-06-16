import os
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
from xpdacq.glbl import glbl
glbl._dark_dict_list = []

import yaml
import inspect
from .yamldict import YamlDict, YamlChainMap
from xpdacq.validated_dict import ValidatedDictLike

verify_files_saved = MagicMock()


# This is used to map plan names (strings in the YAML file) to actual
# plan functions in Python.
_PLAN_REGISTRY = {}

from bluesky.examples import motor, det, Reader


class FakeSignal(MagicMock):
    def get(self):
        return 5

class SimulatedPE1C(Reader):
    "Subclass the bluesky plain detector examples ('Reader'); add attributes."
    def __init__(self, name, fields):
        self.images_per_set = MagicMock()
        self.images_per_set.get = MagicMock(return_value=5)
        self.number_of_sets = MagicMock()
        self.number_of_sets.put = MagicMock(return_value=1)
        self.number_of_sets.get = MagicMock(return_value=1)
        self.cam = MagicMock()
        self.cam.acquire_time = MagicMock()
        self.cam.acquire_time.put = MagicMock(return_value=0.1)
        self.cam.acquire_time.get = MagicMock(return_value=0.1)

        super().__init__(name, fields)

        self.ready = True  # work around a hack in Reader


def setup_module():
    glbl.pe1c = SimulatedPE1C('pe1c', ['pe1c'])
    glbl.shutter = motor  # this passes as a fake shutter
    glbl.frame_acq_time = 0.1
    glbl._dark_dict_list = []

setup_module()

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


def use_photon_shutter():
    glbl.shutter = 'foo'


def use_fast_shutter():
    glbl.shutter = 'fastfoo'


def _stash_uid(name, doc):
    # intercept the uid of a dark frame and stash it
    if name == 'start':
        glbl.last_dark_frame_uid = doc['uid']


def _update_dark_dict_list(name, doc):
    """ generate dark frame reference

    This function should be subscribed to 'stop' documents from dark
    frame runs.
    """
    # always grab from glbl state 
    dark_dict_list = list(glbl._dark_dict_list)
    # obtain light count time that is already set to glbl.pe1c
    acq_time = glbl.pe1c.cam.acquire_time.get()
    num_frame = glbl.pe1c.images_per_set.get()
    light_cnt_time = acq_time * num_frame

    dark_dict = {}
    dark_dict['exposure'] = light_cnt_time
    dark_dict['timestamp'] = doc['time']
    dark_dict['uid'] = doc['run_start']
    dark_dict_list.append(dark_dict)
    glbl._dark_dict_list = dark_dict_list # update glbl._dark_dict_list


def take_dark():
    "a plan for taking a single dark frame"
    print('closing shutter...')
    yield from bp.abs_set(glbl.shutter, 0)
    yield from bp.sleep(2)
    print('taking dark frame....')
    # upto this stage, glbl.pe1c has been configured to so exposure time is
    # correct
    c = bp.count([glbl.pe1c], md={'dark_frame': True})
    yield from bp.subs_wrapper(c, {'stop': [_update_dark_dict_list]})
    print('opening shutter...')
    yield from bp.abs_set(glbl.shutter, 1)
    yield from bp.sleep(2)


def periodic_dark(plan):
    """
    a plan wrapper that takes a plan and inserts `take_dark`

    The `take_dark` plan is inserted on the fly before the beginning of
    any new run after a period of time defined by `glbl.dk_window` has passed.
    """
    need_dark = True

    def insert_take_dark(msg):
        now = time.time()
        nonlocal need_dark
        qualified_dark_uid = _validate_dark(expire_time=glbl.dk_window)

        # FIXME: should we do "or" or "and"?
        if ((not need_dark) and (not qualified_dark_uid)):
            need_dark = True
        if need_dark and msg.command == 'open_run' and ('dark_frame' not
                in msg.kwargs):
            # We are about to start a new 'run' (e.g., a count or a scan).
            # Insert a dark frame run first.
            need_dark = False
            return bp.pchain(take_dark(), bp.single_gen(msg)), None
        else:
            # do nothing if (not need_dark)
            return None, None


    return (yield from bp.plan_mutator(plan, insert_take_dark))


def _validate_dark(expire_time=None):
    """ find appropriate dark frame uid stored in dark_dict_list

    element in dark_scan_dict is expected to be a dict with following
    keys: 'exposure', 'uid' and 'timestamp'

    """
    if expire_time is None:
        expire_time = glbl.dk_window
    dark_dict_list = glbl._dark_dict_list
    # print('my dark_dict_list is {}'.format(dark_dict_list))
    # print('dark_dict_list is False = {}'.format(dark_dict_list is False))
    if not dark_dict_list:
        return None
    # obtain light count time that is already set to pe1c
    acq_time = glbl.pe1c.cam.acquire_time.get()
    num_frame = glbl.pe1c.images_per_set.get()
    light_cnt_time = acq_time * num_frame
    # find fresh and qualified dark
    now = time.time()
    qualified_dark_uid = [ el['uid'] for el in dark_dict_list if
                         abs(el['exposure'] - light_cnt_time) <= acq_time and
                         abs(el['timestamp'] - now) <= (expire_time - acq_time)
                         ]
    if qualified_dark_uid:
        return qualified_dark_uid[-1]
    else :
        return None


def _inject_last_dark_frame_uid(msg):
    if msg.command == 'open_run' and msg.kwargs.get('dark_frame') != True:
        msg.kwargs['dark_frame'] = glbl.last_dark_frame_uid
    return msg


def _inject_qualified_dark_frame_uid(msg):
    if msg.command == 'open_run' and msg.kwargs.get('dark_frame') != True:
        dark_uid = _validate_dark(glbl.dk_window)
        msg.kwargs['dark_frame_uid'] = dark_uid
    return msg


class CustomizedRunEngine(RunEngine):
    def __init__(self, beamtime, *args, **kwargs):
        """
        A RunEngine customized for XPD workflows.

        Parameters
        ----------
        beamtime : Beamtime

        Examples
        --------
        Automatic configuration during startup process...
        >>> bt = load_beamtime('some/directory/pi_name')
        >>> prun = CustomizedRunEngine(bt)

        Basic usage...
        >>> prun(3, 'ct')  # Do an XPD count ('ct') plan on Sample 3.

        Advanced usage...

        Use custom plans
        >>> prun(3, custom_plan)  # sample 3, an arbitrary bluesky plan

        Or custom sample info --- sample just has to be dict-like
        and contain the required keys.
        >>> prun(custom_sample_dict, custom_plan)

        Customize dark frame period
        >>> prun(3, 'ct', dark_strategy=partial(periodic_dark, period=1000)

        Or use completely custom dark frame logic
        >>> prun(3, 'ct', dark_strategy=some_custom_func)
        """
        super().__init__(*args, **kwargs)
        self.beamtime = beamtime

    def __call__(self, sample, plan, subs=None, *,
                 verify_write=False, dark_strategy=periodic_dark,
                 raise_if_interrupted=False, **metadata_kw):
        # The CustomizedRunEngine knows about a Beamtime object, and it
        # interprets integers for 'sample' as indexes into the Beamtime's
        # lists of Samples from all its Experiments.
        if isinstance(sample, int):
            sample = self.beamtime.samples[sample]
        # If a plan is given as a string, look in up in the global registry.
        if isinstance(plan, str):
            plan = _PLAN_REGISTRY[plan]
        # If the plan is an xpdAcq 'ScanPlan', make the actual plan.
        if isinstance(plan, ScanPlan):
            plan = plan.factory()
        _subs = normalize_subs_input(subs)
        if verify_write:
            _subs.update({'stop': verify_files_saved})
        # No keys in metadata_kw are allows to collide with sample keys.
        if set(sample) & set(metadata_kw):
            raise ValueError("These keys in metadata_kw are illegal "
                             "because they are always in sample: "
                             "{}".format(set(sample) & set(metadata_kw)))
        metadata_kw.update(sample)
        sh = glbl.shutter
        # force to open shutter before scan and close it after
        plan = bp.pchain(bp.abs_set(sh, 1), plan, bp.abs_set(sh, 0))
        # Alter the plan to incorporate dark frames.
        plan = dark_strategy(plan)
        plan = bp.msg_mutator(plan, _inject_qualified_dark_frame_uid)
        super().__call__(plan, subs,
                         raise_if_interrupted=raise_if_interrupted,
                         **metadata_kw)

def _configure_pe1c(exposure):
    """ priviate function to configure pe1c with continuous acquistion
    mode"""
    # TODO maybe move it into glbl?
    # setting up detector
    glbl.pe1c.number_of_sets.put(1)
    glbl.pe1c.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = glbl.pe1c.cam.acquire_time.get()
    # compute number of frames
    num_frame = np.ceil(exposure / acq_time)
    if num_frame == 0:
        num_frame = 1
    computed_exposure = num_frame*acq_time
    glbl.pe1c.images_per_set.put(num_frame)
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
                        # 'sp_name': 'ct_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'plan_name': 'ct'})
    plan = bp.count([pe1c], md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([pe1c]))
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
                        # 'sp_name': 'Tramp_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'plan_name': 'Tramp'})
    plan = bp.scan([pe1c], cs700, Tstart, Tstop, Nsteps, md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([pe1c, cs700]))
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
                        'plan_name': 'tseries'})

    plan = bp.count([pe1c], num, delay, md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([pe1c]))
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


def new_short_uid():
    return str(uuid.uuid4())[:8]


class Beamtime(ValidatedDictLike, YamlDict):
    _REQUIRED_FIELDS = ['pi_name', 'safnum']

    def __init__(self, pi_name, safnum, **kwargs):
        super().__init__(pi_name=pi_name, safnum=safnum, **kwargs)
        self.experiments = []
        self._referenced_by = self.experiments  # used by YamlDict
        self.setdefault('beamtime_uid', new_short_uid())

    @property
    def samples(self):
        "a flattened list of all the samples from all the experiments"
        return [s for e in self.experiments for s in e.samples]

    def validate(self):
        # This is automatically called whenever the contents are changed.
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return '{pi_name}/beamtime.yml'.format(**self)

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
        return cls(pi_name=d.pop('pi_name'),
                   safnum=d.pop('safnum'),
                   beamtime_uid=d.pop('beamtime_uid'),
                   **d)

    def __str__(self):
        contents = (['Experiments:'] +
                    ['{i}: {experiment_name}'.format(i=i, **e)
                     for i, e in enumerate(self.experiments)] +
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
        self.samples = []
        self._referenced_by = self.samples  # used by YamlDict
        self.setdefault('experiment_uid', new_short_uid())
        beamtime.register_experiment(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join('{pi_name}', 'experiments',
                            '{experiment_name}.yml').format(**self)

    def register_sample(self, sample):
        # Notify this Experiment about an Sample that should be re-synced
        # whenever the contents of the Experiment are edited.
        self.samples.append(sample)

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
        return cls(experiment_name=map1.pop('experiment_name'),
                   beamtime=beamtime,
                   experiment_uid=map1.pop('experiment_uid'),
                   **map1)


class Sample(ValidatedDictLike, YamlChainMap):
    _REQUIRED_FIELDS = ['name', 'composition']

    def __init__(self, name, experiment, *, composition, **kwargs):
        experiment.register_sample(self)
        sample = dict(name=name, composition=composition, **kwargs)
        super().__init__(sample, *experiment.maps)
        self.experiment = experiment
        self.setdefault('sample_uid', new_short_uid())

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join('{pi_name}', 'samples',
                            '{name}.yml').format(**self)

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
        return cls(name=map1.pop('name'),
                   experiment=experiment,
                   sample_uid=map1.pop('sample_uid'),
                   **map1)

class ScanPlan(ValidatedDictLike, YamlChainMap):
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


def load_beamtime(directory):
    """
    Load a Beamtime and associated objects.

    Expected directory structure:
    directory/
      beamtime.yml
      samples/
      experiments/
    """
    known_uids = {}
    beamtime_fn = os.path.join(directory, 'beamtime.yml')
    experiment_fns = os.listdir(os.path.join(directory, 'experiments'))
    sample_fns = os.listdir(os.path.join(directory, 'samples'))

    with open(beamtime_fn, 'r') as f:
        bt = load_yaml(f, known_uids)

    for fn in experiment_fns:
        with open(os.path.join(directory, 'experiments', fn), 'r') as f:
            load_yaml(f, known_uids)

    for fn in sample_fns:
        with open(os.path.join(directory, 'samples', fn), 'r') as f:
            load_yaml(f, known_uids)

    return bt


def load_yaml(f, known_uids=None):
    """
    Recreate a Sample, Experiment, or Beamtime object from a YAML file.

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
        obj = Sample.from_yaml(f, experiment=experiment, beamtime=beamtime)
        known_uids[obj['sample_uid']] = obj
    else:
        raise ValueError("File does not match a recognized specification.")
    return obj


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
register_plan('Tramp', Tramp)
register_plan('tseries', tseries)
