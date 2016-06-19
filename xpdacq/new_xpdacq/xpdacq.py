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

# FIXME use exact import after entire cleaning
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

        Inspect avaiable experiments, samples, plans.
        >>> print(bt)
        Experiments:
        0: another_test

        ScanPlans:
        0: (...summary of scanplan...)

        Samples:
        0: name

        Run samples and plans by number...
        >>> prun(0, 0)

        ... or by name.
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
            # e.g., 'ct'
            plan = _PLAN_REGISTRY[plan]
        elif isinstance(plan, int):
            plan = self.beamtime.scanplans[plan]
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


register_plan('ct', ct)
register_plan('Tramp', Tramp)
register_plan('tseries', tseries)
