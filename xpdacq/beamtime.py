import os
import uuid
import yaml
import inspect
from collections import ChainMap
import bluesky.plans as bp
import numpy as np
from bluesky.callbacks import LiveTable

from .glbl import glbl
from .yamldict import YamlDict, YamlChainMap
from .validated_dict import ValidatedDictLike

# This is used to map plan names (strings in the YAML file) to actual
# plan functions in Python.
_PLAN_REGISTRY = {}


def register_plan(plan_name, plan_func, overwrite=False):
    """
    Map between a plan_name (string) and a plan_func (generator function).
    """
    if plan_name in _PLAN_REGISTRY and not overwrite:
        raise KeyError("A plan is already registered by this name. Use "
                       "overwrite=True to overwrite it.")
    _PLAN_REGISTRY[plan_name] = plan_func


def unregister_plan(plan_name):
    del _PLAN_REGISTRY[plan_name]


def _summarize(plan):
    """based on bluesky.utils.print_summary"""
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
    """
    private function to configure pe1c with continuous acquisition mode
    """
    # cs studio configuration doesn't propagate to python level
    glbl.area_det.cam.acquire_time.put(glbl.frame_acq_time)
    # compute number of frames
    acq_time = glbl.area_det.cam.acquire_time.get()
    _check_mini_expo(exposure, acq_time)
    num_frame = np.ceil(exposure / acq_time)
    computed_exposure = num_frame * acq_time
    glbl.area_det.images_per_set.put(num_frame)
    # print exposure time
    print("INFO: requested exposure time = {} - > computed exposure time"
          "= {}".format(exposure, computed_exposure))
    return num_frame, acq_time, computed_exposure


def _check_mini_expo(exposure, acq_time):
    if exposure < acq_time:
        raise ValueError("WARNING: total exposure time: {}s is shorter "
                         "than frame acquisition time {}s\n"
                         "you have two choices:\n"
                         "1) increase your exposure time to be at least"
                         "larger than frame acquisition time\n"
                         "2) increase the frame rate, if possible\n"
                         "    - to increase exposure time, simply resubmit"
                         "    the ScanPlan with a longer exposure time\n"
                         "    - to increase frame-rate/decrease the"
                         "    frame acquisition time, please use the"
                         "    following command:\n"
                         "    >>> {} \n then rerun your ScanPlan definition"
                         "    or rerun the xrun"
                         "Note: by default, xpdAcq recommends running"
                         "the detector at  its fastest frame-rate\n"
                         "(currently with a frame-acquisition time of"
                         "0.1s)\n in which case you cannot set it to a"
                         "lower value"
                         .format(exposure, acq_time,
                                 ">>> glbl.frame_acq_time = 0.5  #set"
                                 " to 0.5s"))

def ct(dets, exposure, *, md=None):
    """
    Take one reading from area detectors with given exposure time

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    exposure : float
        total time of exposrue in seconds
    md : dict, optional
        extra metadata

    Note
    ----
    area detector that is triggered will always be the one configured in
    global state. Please refer to http://xpdacq.github.io for more information
    """

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
                        'sp_plan_name': 'ct'})
    plan = bp.count([glbl.area_det], md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det]))
    yield from plan


def Tramp(dets, exposure, Tstart, Tstop, Tstep, *, md=None):
    """
    Scan over temeprature controller in steps.

    temeprature steps are defined by starting point,
    stoping point and step size

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    exposure : float
        exposure time at each temeprature step in seconds
    Tstart : float
        starting point of temperature sequence
    Tstop : float
        stoping point of temperature sequence
    Tstep : float
        step size between Tstart and Tstop of this sequence
    md : dict, optional
        extra metadata

    Note
    ----
    temperature controller that is driven will always be the one configured in
    global state. Please refer to http://xpdacq.github.io for more information
    """

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
                        'sp_plan_name': 'Tramp'})
    plan = bp.scan([glbl.area_det], glbl.temp_controller, Tstart, Tstop,
                   Nsteps, md=_md)
    plan = bp.subs_wrapper(plan,
                           LiveTable([glbl.area_det, glbl.temp_controller]))
    yield from plan


def Tlist(dets, exposure, T_list):
    """defines a flexible scan with user-specified temperatures

    A frame is exposed for the given exposure time at each of the
    user-specified temperatures

    Parameters
    ----------
    dets : list
        list of objects that represent instrument devices. In xpdAcq, it is
        defaulted to area detector.
    exposure : float
        total time of exposure in seconds for area detector
    T_list : list
        a list of temperatures where a scan will be run

    Note
    ----
    area detector and temperature controller will always be the one
    configured in global state. To find out which these are, please
    using following commands:

        >>> glbl.area_det
        >>> glbl.temp_controller

    To interrogate which devices are currently in use.
    """

    pe1c, = dets
    # setting up area_detector and temp_controller
    (num_frame, acq_time, computed_exposure) = _configure_pe1c(exposure)
    T_controller = glbl.temp_controller
    xpdacq_md = {'sp_time_per_frame': acq_time,
                 'sp_num_frames': num_frame,
                 'sp_requested_exposure': exposure,
                 'sp_computed_exposure': computed_exposure,
                 'sp_T_list': T_list,
                 'sp_type': 'Tlist',
                 'sp_uid': str(uuid.uuid4()),
                 'sp_plan_name': 'Tlist'
                }
    # pass xpdacq_md to as additional md to bluesky plan
    plan = bp.list_scan([glbl.area_det], T_controller, T_list, md=xpdacq_md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det, T_controller]))
    yield from plan


def tseries(dets, exposure, delay, num, *, md=None):
    """
    time series scan with area detector.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    exposure : float
        exposure time at each reading from area detector in seconds
    delay : float
        delay between two adjustant reading from area detector in seconds
    num : int
        total number of readings
    md : dict, optional
        metadata

    Note
    ----
    area detector that is triggered will always be the one configured in
    global state. Please refer to http://xpdacq.github.io for more information
    """

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
                        'sp_requested_delay': delay,
                        'sp_requested_num': num,
                        'sp_type': 'tseries',
                        # need a name that shows all parameters values
                        # 'sp_name': 'tseries_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'sp_plan_name': 'tseries'})
    plan = bp.count([glbl.area_det], num, delay, md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([glbl.area_det]))
    yield from plan


def _nstep(start, stop, step_size):
    """ helper function to compute number of steps and step_size
    """
    requested_nsteps = abs((start - stop) / step_size)

    computed_nsteps = int(requested_nsteps) + 1  # round down for a finer step
    computed_step_list = np.linspace(start, stop, computed_nsteps)
    computed_step_size = computed_step_list[1] - computed_step_list[0]
    print("INFO: requested temperature step size = {} ->"
          "computed temperature step size = {}"
          .format(step_size, computed_step_size))
    return computed_nsteps, computed_step_size


register_plan('ct', ct)
register_plan('Tramp', Tramp)
register_plan('tseries', tseries)
register_plan('Tlist', Tlist)


def new_short_uid():
    return str(uuid.uuid4())[:8]


def _clean_info(obj):
    """ stringtify and replace space"""
    return str(obj).strip().replace(' ', '_')


class Beamtime(ValidatedDictLike, YamlDict):
    """
    class that carries necessary information for a beamtime

    Parameters
    ----------
    pi_last : str
        last name of PI to this beamtime.
    saf_num : int
        Safty Approval Form number to current beamtime.
    experimenters : list, optional
        list of experimenter names. Each of experimenter name is
        expected to be comma separated as `first_name', `last_name`.
    wavelength : float, optional
        wavelength of current beamtime, in angstrom.
    kwargs :
        extra keyword arguments for current beamtime.

    Examples
    --------
    Inspect avaiable samples, plans.
    >>> print(bt)
    ScanPlans:
    0: (...summary of scanplan...)

    Samples:
    0: (...name of sample...)

    or equivalently
    >>> bt.list()
    ScanPlans:
    0: (...summary of scanplan...)

    Samples:
    0: (...name of sample...)
    """

    _REQUIRED_FIELDS = ['bt_piLast', 'bt_safN']

    def __init__(self, pi_last, saf_num, experimenters=[], *,
                 wavelength=None, **kwargs):
        super().__init__(bt_piLast=_clean_info(pi_last),
                         bt_safN=_clean_info(saf_num),
                         bt_experimenters=experimenters,
                         bt_wavelength=wavelength, **kwargs)
        self._wavelength = wavelength
        # self.experiments = []
        self.scanplans = []
        self.samples = []
        self._referenced_by = []
        # used by YamlDict
        self.setdefault('bt_uid', new_short_uid())

    @property
    def wavelength(self):
        """ wavelength value of current beamtime. updated value will be
        passed down to all related objects"""
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val):
        self._wavelength = val
        self.update(bt_wavelength=val)

    def register_scanplan(self, scanplan):
        # Notify this Beamtime about an ScanPlan that should be re-synced
        # whenever the contents of the Beamtime are edited. 
        sp_name_list = [el.short_summary() for el in self.scanplans]
        # manage bt.list
        if scanplan.short_summary() not in sp_name_list:
            self.scanplans.append(scanplan)
        else:
            old_obj = [obj for obj in self.scanplans if
                       obj.short_summary() == scanplan.short_summary()].pop()
            old_obj_ind = self.scanplans.index(old_obj)
            self.scanplans.remove(old_obj)
            self.scanplans.insert(old_obj_ind, scanplan)
        # yaml sync list
        # simply append object to list to increase speed
        #self._referenced_by.extend([el for el in self.scanplans if el
        #                            not in self._referenced_by])
        self._referenced_by.append(scanplan)

    @property
    def md(self):
        """ metadata of current object """
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
        sa_name_list = [el.get('sample_name', None) for el in self.samples]
        # manage bt.list
        if sample.get('sample_name') not in sa_name_list:
            self.samples.append(sample)
        else:
            old_obj = [obj for obj in self.samples if obj.get('sample_name') ==
                       sample.get('sample_name')].pop()
            old_obj_ind = self.samples.index(old_obj)
            self.samples.remove(old_obj)
            self.samples.insert(old_obj_ind, sample)
        # yaml sync list
        # simply append object to list to increase speed
        # filtering logic is handle when importing sample
        #self._referenced_by.extend([el for el in self.samples if el
        #                            not in self._referenced_by])
        # simply append object to list to increase speed
        # filtering logic is handle when importing sample
        self._referenced_by.append(sample)

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
                    ['{i}: {sample_name}'.format(i=i, **s)
                     for i, s in enumerate(self.samples)])
        return '\n'.join(contents)

    def list(self):
        """ method to list out all ScanPlan and Sample objects related
        to this Beamtime object
        """
        # for back-compat
        print(self)

    def list_bkg(self):
        """ method to list background object only """

        contents = ['', 'Background:'] + ['{i}: {sample_name}'.format(i=i, **s)
                                          for i, s in enumerate(self.samples)
                                          if s['sample_name'].startswith('bkgd')]
        print('\n'.join(contents))

class Sample(ValidatedDictLike, YamlChainMap):
    """
    class that carries sample-related metadata

    after creation, this Sample object will be related to Beamtime
    object given as argument and will be available in bt.list()

    Parameters
    ----------
    beamtime : xpdacq.beamtime.Beamtime
        object representing current beamtime
    sample_md : dict
        dictionary contains all sample related metadata
    kwargs :
        keyword arguments for extr metadata

    Examples
    --------
    >>> Sample(bt, {'sample_name': 'Ni', 'sample_composition':{'Ni': 1}})

    >>> Sample(bt, {'sample_name': 'TiO2',
                    'sample_composition':{'Ti': 1, 'O': 2}})

    Please refer to http://xpdacq.github.io for more examples.
    """

    _REQUIRED_FIELDS = ['sample_name', 'sample_composition']

    def __init__(self, beamtime, sample_md, **kwargs):
        composition = sample_md.get('sample_composition', None)
        # print("composition of {} is {}".format(sample_md['sample_name'],
        #                                       sample_md['sample_composition']))
        try:
            super().__init__(sample_md, beamtime)  # ChainMap signature
        except:
            print("At least sample_name and sample_composition is needed.\n"
                  "For example\n"
                  ">>> sample_md = {'sample_name':'Ni',"
                  "'sample_composition':{'Ni':1}}\n"
                  ">>> Sample(bt, sample_md)\n")
            return
        self.setdefault('sa_uid', new_short_uid())
        beamtime.register_sample(self)

    def validate(self):
        missing = set(self._REQUIRED_FIELDS) - set(self)
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

    def default_yaml_path(self):
        return os.path.join(glbl.yaml_dir, 'samples',
                            '{sample_name}.yml').format(**self)

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
        # uid = map1.pop('sa_uid')
        return cls(beamtime, map1,
                   # sa_uid=uid,
                   **map1)


class ScanPlan(ValidatedDictLike, YamlChainMap):
    """
    class that carries scan plan with corresponding experimental arguements

    after creation, this Sample object will be related to Beamtime
    object given as argument and will be available in bt.list()

    Parameters
    ----------
    beamtime : xpdacq.beamtime.Beamtime
        object representing current beamtime.
    plan_func :
        predefined plan function. For complete list of available functions,
        please refere to http://xpdacq.github.io for more information.
    args :
        positional arguments corresponding to plan function in used.
    kwargs :
        keyword arguments corresponding to plan function in used.

    Examples
    --------
    A `ct` (count) scan with 5s exposure time linked to Beamtime object `bt`.
    >>> ScanPlan(bt, ct, 5)

    `ScanPlan` class also takes keyword arguments.
    >>> ScanPlan(bt, ct, exposure=5)

    Please refer to http://xpdacq.github.io for more examples.
    """

    def __init__(self, beamtime, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        plan_name = plan_func.__name__
        sp_dict = {'sp_plan_name': plan_name, 'sp_args': args,
                   'sp_kwargs': kwargs}
        if 'sp_uid' in sp_dict['sp_kwargs']:
            scanplan_uid = sp_dict['sp_kwargs'].pop('sp_uid')
            sp_dict.update({'sp_uid': scanplan_uid})
        # test if that is a valid plan
        exposure = kwargs.get('exposure') # input as kwargs
        if exposure is None:
            # input as args
            exposure, *rest = args  # predefined scan signature
        _check_mini_expo(exposure, glbl.frame_acq_time)
        super().__init__(sp_dict, beamtime)  # ChainMap signature
        self.setdefault('sp_uid', new_short_uid())
        beamtime.register_scanplan(self)

    @property
    def md(self):
        """ metadata for current object """
        open_run, = [msg for msg in self.factory() if
                     msg.command == 'open_run']
        return open_run.kwargs

    @property
    def bound_arguments(self):
        """ bound arguments of this ScanPlan object """
        signature = inspect.signature(self.plan_func)
        # empty list is for [pe1c]
        bound_arguments = signature.bind([], *self['sp_args'],
                                         **self['sp_kwargs'])
        # bound_arguments.apply_defaults() # only valid in py 3.5
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
        sp_kwargs.update({'sp_uid': plan_uid})
        return cls(beamtime, plan_func, *sp_args, **sp_kwargs)

    def default_yaml_path(self):
        arg_value_str = map(str, self.bound_arguments.values())
        fn = '_'.join([self['sp_plan_name']] + list(arg_value_str))
        return os.path.join(glbl.yaml_dir, 'scanplans',
                            '%s.yml' % fn)
