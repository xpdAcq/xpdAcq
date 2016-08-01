import os
import yaml
import shutil
import unittest
from mock import MagicMock

from xpdacq.new_xpdacq.glbl import glbl
from xpdacq.new_xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime,
                                             load_beamtime)
from xpdacq.new_xpdacq.beamtime import (_summarize, ScanPlan, ct, Tramp,
                                        tseries, Beamtime, Experiment, Sample)

from bluesky.examples import motor, det, Reader

#prun = CustomizedRunEngine({}, {})
# print messages for debugging
#prun.msg_hook = print

class BeamtimeObjTest(unittest.TestCase):

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.config_dir = os.path.join(self.base_dir,'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = '123'   # must be 123 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),
                              ('Terban ',' Max',2)]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        self.ex = Experiment('temp_test', self.bt)
        self.sa = Sample('test_sample', self.bt, composition={'Ni':1})

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir,'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir,'pe2_data'))


    def test_print_scanplan(self):
        # using positional args
        sp1 = ScanPlan(self.bt.experiments[0], ct, 1)
        # using kwargs is equivalent
        sp2 = ScanPlan(self.bt.experiments[0], ct, exposure=1)
        # test Msg processed
        self.assertEqual(str(sp1),str(sp2))


    @unittest.skip
    def test_run_scanplan(self):
        sp = ScanPlan(ct, 1)
        prun({}, sp)


    def test_ct_scanplan_autoname(self):
        sp = ScanPlan(self.bt.experiments[0], ct, 1)
        #std_f_name = 'ct_1_None.yml' #py3.4 only gets args
        std_f_name = 'ct_1.yml' #py3.4 only gets args
        yaml_name = os.path.basename(sp.default_yaml_path())
        self.assertEqual(yaml_name, std_f_name)

    def test_ct_scanplan_md(self):
        sp = ScanPlan(self.bt.experiments[0], ct, 1)
        sp_md = dict(sp)
        # md to scanplan itself
        self.assertEqual(sp_md['sp_plan_name'], 'ct')
        self.assertTrue('sp_uid' in sp_md)
        self.assertTrue(1 in sp_md['sp_args'])
        # scanplan knows bt
        for k,v in dict(self.bt).items():
            self.assertEqual(sp_md[k],v)
        # scanplan knows experiment
        for k,v in dict(self.ex).items():
            self.assertEqual(sp_md[k],v)

    def test_scanplan_yamlize(self):
        sp = ScanPlan(self.bt.experiments[0], ct, 1)
        # bound arguments
        #expected_bound_args = {'exposure': 1, 'md': None} 
        expected_bound_args = {'exposure': 1} #py3.4 only get args
        self.assertEqual(dict(sp.bound_arguments),
                         expected_bound_args)
        # reload
        reload_dict = yaml.load(sp.to_yaml())
        self.assertEqual(len(reload_dict), 3) # sp, ex, bt
        ## contents of chainmap
        self.assertEqual(reload_dict[0], sp.maps[0])
        self.assertEqual(reload_dict[1], sp.maps[1])
        self.assertEqual(reload_dict[2], sp.maps[2])

        # equality
        reload_scanplan = ScanPlan.from_yaml(sp.to_yaml())
        other_sp = ScanPlan(self.bt.experiments[0], ct, 5)
        self.assertFalse(sp == other_sp)
        #self.assertTrue(sp == reload_scanplan)

    def test_beamtime_roundtrip(self):
        # This includes checking that a new uid is only generated once
        # and persists thereafter.
        bt = Beamtime('Simon', '123', [], wavelength=0.1828)
        reloaded_bt = Beamtime.from_yaml(bt.to_yaml())
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt, bt)


    def test_experiment_roundtrip(self):
        bt = Beamtime('Simon', '123', [], wavelength=0.1828)
        ex = Experiment('test-experiment', bt)
        reloaded_ex = Experiment.from_yaml(ex.to_yaml())
        os.remove(bt.filepath)
        os.remove(ex.filepath)
        self.assertEqual(reloaded_ex, ex)

    def test_sample_roundtrip(self):
        bt = Beamtime('Simon', '123', [], wavelength=0.1828)
        ex = Experiment('test-experiment', bt)
        sam = Sample('test-sample', bt, composition={'vapor':1})
        reloaded_sam = Sample.from_yaml(sam.to_yaml())
        os.remove(bt.filepath)
        os.remove(ex.filepath)
        os.remove(sam.filepath)
        self.assertEqual(reloaded_sam, sam)


    def test_scanplan_roundtrip(self):
        bt = Beamtime('Simon', '123', [], wavelength=0.1828)
        ex = Experiment('test-experiment', bt)
        sp = ScanPlan(self.bt.experiments[0], ct, 1)
        reload_sp = ScanPlan.from_yaml(sp.to_yaml())
        self.assertEqual(reload_sp, sp)
        #reload_scanplan = ScanPlan.from_yaml(sp.to_yaml())
        #print('reload scanplan = {}'
        #      .format(reload_scanplan))
        #print('scanplan = {}'.format(sp.maps))
        # from_yaml
        #self.assertEqual(len(yaml.load(reload_scanplan.to_yaml())), 3)
        #print('reload scanplan = {}'
        #      .format(yaml.load(reload_scanplan.to_yaml())))
        #print('scanplan = {}'.format(sp.maps))
        #self.assertEqual(yaml.load(reload_scanplan.to_yaml())[0],
        #                 sp.maps[0])
        #self.assertEqual(yaml.load(reload_scanplan.to_yaml())[1],
        #                 sp.maps[1])
        #self.assertEqual(yaml.load(reload_scanplan.to_yaml())[2],
        #                 sp.maps[2])

    def test_yaml_sync(self):
        "Updating the object immediately, automatically updates the file."

        # Adding a field syncs
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_update='before')
        bt['new_field'] = 'test'
        with open(bt.filepath, 'r') as f:
            reloaded_bt = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt['new_field'], 'test')
        self.assertEqual(reloaded_bt, bt)

        # Setting to an existing field syncs
        #bt = Beamtime('Simon', 123, field_to_update='before')
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_update='before')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt['field_to_update'] = 'after'
        with open(bt.filepath, 'r') as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt_before_change['field_to_update'],
                         'before')
        self.assertEqual(reloaded_bt_after_change['field_to_update'],
                         'after')
        self.assertEqual(reloaded_bt_after_change, bt)

        # Updating syncs
        #bt = Beamtime('Simon', 123, field_to_update='before')
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_update='before')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt.update(field_to_update='after')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt_before_change['field_to_update'],
                                                   'before')
        self.assertEqual(reloaded_bt_after_change['field_to_update'],
                                                  'after')
        self.assertEqual(reloaded_bt_after_change, bt)

        # Deleting a field syncs
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_remove='before')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        del bt['field_to_remove']
        with open(bt.filepath, 'r') as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertTrue('field_to_remove' in reloaded_bt_before_change)
        self.assertTrue('field_to_remove' not in
                        reloaded_bt_after_change)
        self.assertEqual(reloaded_bt_after_change, bt)

        # Popping a field syncs
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_remove='before')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt.pop('field_to_remove')
        with open(bt.filepath, 'r') as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(self.bt.filepath)
        self.assertTrue('field_to_remove' in reloaded_bt_before_change)
        self.assertTrue('field_to_remove' not in reloaded_bt_after_change)
        self.assertEqual(reloaded_bt_after_change, bt)

        # setdefault syncs
        bt = Beamtime('Simon', '123', [], wavelength=0.1828,
                      field_to_update='before')
        bt.setdefault('new_field', 'test')
        with open(bt.filepath, 'r') as f:
            reloaded_bt = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt['new_field'], 'test')
        self.assertEqual(reloaded_bt, bt)


    def test_yaml_sync_between_objects(self):
        "Updating a Beamtime updates Experiment(s) and Sample(s)"
        "that refer to it"

        self.bt['new_bt_field'] = 'test'
        # Experiment and Sample should be automatically synced.
        with open(self.ex.filepath, 'r') as f:
            reloaded_ex = self.ex.from_yaml(f)
        with open(self.sa.filepath, 'r') as f:
            reloaded_sa = self.sa.from_yaml(f)
        self.assertTrue('new_bt_field' in reloaded_ex)
        self.assertTrue('new_bt_field' in reloaded_sa)


    def test_chaining(self):
        "All contents of Beamtime and Experiment should propagate into Sample."
        bt =  Beamtime('Simon', 123, [], wavelength=0.1828, custom1='A')
        ex = Experiment('test-experiment', bt, custom2='B')
        sa = Sample('test-sample', bt, composition={'vapor':1}, custom3='C')
        for k, v in bt.items():
            ex[k] == bt[k]
            sa[k] == bt[k]


    def test_load_beamtime(self):
        bt =  Beamtime('Simon', 123, [], wavelength=0.1828, custom1='A')
        ex = Experiment('test-experiment', bt, custom2='B')
        sa = Sample('test-sample', bt, composition={'vapor':1}, custom3='C')

        bt2 = load_beamtime()
        self.assertEqual(bt2, bt)
        self.assertEqual(bt2.experiments[0], ex)
        self.assertEqual(bt2.samples[0], sa)
