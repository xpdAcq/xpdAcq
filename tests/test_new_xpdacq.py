import os
import yaml
from mock import MagicMock
from xpdacq.new_xpdAcq import (CustomizedRunEngine, ScanPlan, ct, Beamtime,
                               Experiment, Sample, load_beamtime, load_yaml)
from xpdacq.glbl import glbl
from bluesky.examples import motor, det, Reader

prun = CustomizedRunEngine({}, {})
# print messages for debugging
prun.msg_hook = print


class SimulatedPE1C(Reader):
    "Subclass the bluesky plain detector examples ('Reader'); add attributes."
    def __init__(self, name, fields):
        self.images_per_set = MagicMock()
        self.number_of_sets = MagicMock()
        self.cam = MagicMock()
        self.frame_acq_time = MagicMock()
        super().__init__(name, fields)

        self.ready = True  # work around a hack in Reader


def setup_module():
    glbl.pe1c = SimulatedPE1C('pe1c', ['pe1c'])
    glbl.shutter = motor  # this passes as a fake shutter
    glbl.frame_acq_time = 0.1


def test_print_scanplan():
    sp1 = ScanPlan(ct, 1)  # using positional args
    sp2 = ScanPlan(ct, exposure=1)  # using kwargs is equivalent
    assert str(sp1) == str(sp2)


def test_run_scanplan():
    sp = ScanPlan(ct, 1)
    prun({}, sp)


def test_scanplan_autoname():
    sp = ScanPlan(ct, 1)
    std_f_name = 'ct_1_None' 
    assert sp.default_yaml_path() == std_f_name


def test_scanplan_yamlize():
    sp = ScanPlan(ct, 1)
    expected_dict = {'plan_name': 'ct',
                     'plan_args': {'exposure': 1, 'md': None}}
    # reload
    assert yaml.load(sp.to_yaml()) == expected_dict
    # from_yaml
    reload_scanplan = ScanPlan.from_yaml(sp.to_yaml())
    assert yaml.load(reload_scanplan.to_yaml()) == expected_dict
    # equality
    other_sp = ScanPlan(ct, 5)
    assert sp != other_sp
    assert sp == reload_scanplan


def test_beamtime_roundtrip():
    # This includes checking that a new uid is only generated once and
    # persists thereafter.
    bt = Beamtime('Simon', 123)
    reloaded_bt = bt.from_yaml(bt.to_yaml())
    os.remove(bt.filepath)
    assert reloaded_bt == bt


def test_experiment_roundtrip():
    bt = Beamtime('Simon', 123)
    ex = Experiment('test-experiment', bt)
    reloaded_ex = ex.from_yaml(ex.to_yaml())
    os.remove(bt.filepath)
    os.remove(ex.filepath)


def test_sample_roundtrip():
    bt = Beamtime('Simon', 123)
    ex = Experiment('test-experiment', bt)
    sam = Sample('test-sample', ex, composition='vapor')
    reloaded_sam = sam.from_yaml(sam.to_yaml())
    os.remove(bt.filepath)
    os.remove(ex.filepath)
    os.remove(sam.filepath)
    assert reloaded_sam == sam


def test_yaml_sync():
    "Updating the object immediately, automatically updates the file."

    # Adding a field syncs
    bt = Beamtime('Simon', 123)
    bt['new_field'] = 'test'
    with open(bt.filepath, 'r') as f:
        reloaded_bt = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert reloaded_bt['new_field'] == 'test'
    assert reloaded_bt == bt

    # Setting to an existing field syncs
    bt = Beamtime('Simon', 123, field_to_update='before')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_before_change = bt.from_yaml(f)
    bt['field_to_update'] = 'after'
    with open(bt.filepath, 'r') as f:
        reloaded_bt_after_change = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert reloaded_bt_before_change['field_to_update'] == 'before'
    assert reloaded_bt_after_change['field_to_update'] == 'after'
    assert reloaded_bt_after_change == bt

    # Updating syncs
    bt = Beamtime('Simon', 123, field_to_update='before')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_before_change = bt.from_yaml(f)
    bt.update(field_to_update='after')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_after_change = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert reloaded_bt_before_change['field_to_update'] == 'before'
    assert reloaded_bt_after_change['field_to_update'] == 'after'
    assert reloaded_bt_after_change == bt

    # Deleting a field syncs
    bt = Beamtime('Simon', 123, field_to_remove='test')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_before_change = bt.from_yaml(f)
    del bt['field_to_remove']
    with open(bt.filepath, 'r') as f:
        reloaded_bt_after_change = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert 'field_to_remove' in reloaded_bt_before_change
    assert 'field_to_remove' not in reloaded_bt_after_change
    assert reloaded_bt_after_change == bt

    # Popping a field syncs
    bt = Beamtime('Simon', 123, field_to_remove='test')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_before_change = bt.from_yaml(f)
    bt.pop('field_to_remove')
    with open(bt.filepath, 'r') as f:
        reloaded_bt_after_change = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert 'field_to_remove' in reloaded_bt_before_change
    assert 'field_to_remove' not in reloaded_bt_after_change
    assert reloaded_bt_after_change == bt

    # setdefault syncs
    bt = Beamtime('Simon', 123)
    bt.setdefault('new_field', 'test')
    with open(bt.filepath, 'r') as f:
        reloaded_bt = bt.from_yaml(f)
    os.remove(bt.filepath)
    assert reloaded_bt['new_field'] == 'test'
    assert reloaded_bt == bt


def test_yaml_sync_between_objects():
    "Updating a Beamtime updates Experiment(s) and Sample(s) that refer to it"
    bt = Beamtime('Simon', 123)
    ex = Experiment('test-experiment', bt)
    sam = Sample('test-sample', ex, composition='vapor')
    bt['new_bt_field'] = 'test'
    # Experiment and Sample should be automatically synced.
    with open(ex.filepath, 'r') as f:
        reloaded_ex = ex.from_yaml(f)
    with open(sam.filepath, 'r') as f:
        reloaded_sam = sam.from_yaml(f)
    os.remove(bt.filepath)
    os.remove(ex.filepath)
    os.remove(sam.filepath)
    assert 'new_bt_field' in reloaded_ex
    assert 'new_bt_field' in reloaded_sam


def test_chaining():
    "All contents of Beamtime and Experiment should propagate into Sample."
    bt = Beamtime('Simon', 123, custom1='A')
    ex = Experiment('test-experiment', bt, custom2='B')
    sam = Sample('test-sample', ex, composition='vapor', custom3='C')
    for k, v in bt.items():
        ex[k] == bt[k]
        sam[k] == bt[k]
    for k, v in ex.items():
        sam[k] == ex[k]


def test_load_beamtime():
    bt = Beamtime('test-bt', 123)
    ex = Experiment('test-experiment', bt)
    sam = Sample('test-sample', ex, composition='vapor')

    bt2 = load_beamtime('test-bt')
    assert bt2 == bt
    assert bt2.experiments[0] == ex
    assert bt2.experiments[0].samples[0] == sam
