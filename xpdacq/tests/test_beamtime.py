import os
import shutil
import unittest

import yaml
from pkg_resources import resource_filename as rs_fn
from xpdacq.beamtime import Beamtime, Sample, ScanPlan, ct
from xpdacq.beamtimeSetup import _start_beamtime, load_beamtime
from xpdacq.glbl import glbl
from xpdacq.simulation import cs700, db, fb, pe1c, shctl1
from xpdacq.xpdacq import CustomizedRunEngine
from xpdacq.xpdacq_conf import configure_device

# print messages for debugging
# xrun.msg_hook = print


class BeamtimeObjTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl["base"]
        self.home_dir = os.path.join(self.base_dir, "xpdUser")
        self.config_dir = os.path.join(self.base_dir, "xpdConfig")
        self.PI_name = "Billinge "
        # must be 30079 for proper load of config yaml => don't change
        self.saf_num = 30079
        self.wavelength = 0.1812
        self.experimenters = [
            ("van der Banerjee", "S0ham", 1),
            ("Terban ", " Max", 2),
        ]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        # set simulation objects
        configure_device(
            db=db,
            shutter=shctl1,
            area_det=pe1c,
            temp_controller=cs700,
            filter_bank=fb,
        )
        pytest_dir = rs_fn("xpdacq", "tests/")
        config = "XPD_beamline_config.yml"
        configsrc = os.path.join(pytest_dir, config)
        shutil.copyfile(configsrc, os.path.join(glbl["xpdconfig"], config))
        assert os.path.isfile(os.path.join(glbl["xpdconfig"], config))
        self.bt = _start_beamtime(
            self.PI_name,
            self.saf_num,
            self.experimenters,
            wavelength=self.wavelength,
            test=True,
        )
        xlf = "300000_sample.xlsx"
        src = os.path.join(pytest_dir, xlf)
        shutil.copyfile(src, os.path.join(glbl["import_dir"], xlf))

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, "xpdConfig")):
            shutil.rmtree(os.path.join(self.base_dir, "xpdConfig"))
        if os.path.isdir(os.path.join(self.base_dir, "pe2_data")):
            shutil.rmtree(os.path.join(self.base_dir, "pe2_data"))

    def test_ct_scanplan_autoname(self):
        sp = ScanPlan(self.bt, ct, 1)
        # std_f_name = 'ct_1_None.yml' #py3.4 only gets args
        std_f_name = "ct_1.yml"  # py3.4 only gets args
        yaml_name = os.path.basename(sp.default_yaml_path())
        self.assertEqual(yaml_name, std_f_name)

    def test_ct_scanplan_md(self):
        sp = ScanPlan(self.bt, ct, 1)
        sp_md = dict(sp)
        # md to scanplan itself
        self.assertEqual(sp_md["sp_plan_name"], "ct")
        self.assertTrue("sp_uid" in sp_md)
        self.assertTrue(1 in sp_md["sp_args"])
        # scanplan knows bt
        for k, v in dict(self.bt).items():
            self.assertEqual(sp_md[k], v)

    def test_scanplan_yamlize(self):
        sp = ScanPlan(self.bt, ct, 1)
        # bound arguments
        # expected_bound_args = {'exposure': 1, 'md': None}
        expected_bound_args = {"exposure": 1}  # py3.4 only get args
        self.assertEqual(dict(sp.bound_arguments), expected_bound_args)
        # reload
        reload_dict = yaml.unsafe_load(sp.to_yaml())
        self.assertEqual(len(reload_dict), 2)  # bt and sp
        # contents of chainmap
        self.assertEqual(reload_dict[0], sp.maps[0])
        self.assertEqual(reload_dict[1], sp.maps[1])

        # equality
        reload_scanplan = ScanPlan.from_yaml(sp.to_yaml())
        other_sp = ScanPlan(self.bt, ct, 5)
        self.assertFalse(sp == other_sp)
        self.assertTrue(sp == reload_scanplan)

    def test_beamtime_roundtrip(self):
        # This includes checking that a new uid is only generated once
        # and persists thereafter.
        reloaded_bt = Beamtime.from_yaml(self.bt.to_yaml())
        os.remove(self.bt.filepath)
        self.assertEqual(reloaded_bt, self.bt)

    def test_sample_roundtrip(self):
        sa_dict = {"sample_name": "Ni", "sample_composition": {"Ni": 1}}
        sam = Sample(self.bt, sa_dict)
        reloaded_sam = Sample.from_yaml(sam.to_yaml())
        os.remove(self.bt.filepath)
        os.remove(sam.filepath)
        self.assertEqual(reloaded_sam, sam)

    def test_scanplan_roundtrip(self):
        sp = ScanPlan(self.bt, ct, 1)
        reload_sp = ScanPlan.from_yaml(sp.to_yaml())
        self.assertEqual(reload_sp, sp)

    def test_yaml_sync(self):
        """Updating the object immediately, automatically updates the file."""

        # Adding a field syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_update="before"
        )
        bt["new_field"] = "test"
        with open(bt.filepath, "r") as f:
            reloaded_bt = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt["new_field"], "test")
        self.assertEqual(reloaded_bt, bt)

        # Setting to an existing field syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_update="before"
        )
        with open(bt.filepath, "r") as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt["field_to_update"] = "after"
        with open(bt.filepath, "r") as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(
            reloaded_bt_before_change["field_to_update"], "before"
        )
        self.assertEqual(reloaded_bt_after_change["field_to_update"], "after")
        self.assertEqual(reloaded_bt_after_change, bt)

        # Updating syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_update="before"
        )
        with open(bt.filepath, "r") as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt.update(field_to_update="after")
        with open(bt.filepath, "r") as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(
            reloaded_bt_before_change["field_to_update"], "before"
        )
        self.assertEqual(reloaded_bt_after_change["field_to_update"], "after")
        self.assertEqual(reloaded_bt_after_change, bt)

        # Deleting a field syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_remove="before"
        )
        with open(bt.filepath, "r") as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        del bt["field_to_remove"]
        with open(bt.filepath, "r") as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertTrue("field_to_remove" in reloaded_bt_before_change)
        self.assertTrue("field_to_remove" not in reloaded_bt_after_change)
        self.assertEqual(reloaded_bt_after_change, bt)

        # Popping a field syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_remove="before"
        )
        with open(bt.filepath, "r") as f:
            reloaded_bt_before_change = bt.from_yaml(f)
        bt.pop("field_to_remove")
        with open(bt.filepath, "r") as f:
            reloaded_bt_after_change = bt.from_yaml(f)
        os.remove(self.bt.filepath)
        self.assertTrue("field_to_remove" in reloaded_bt_before_change)
        self.assertTrue("field_to_remove" not in reloaded_bt_after_change)
        self.assertEqual(reloaded_bt_after_change, bt)

        # setdefault syncs
        bt = Beamtime(
            "Simon", 123, [], wavelength=0.1828, field_to_update="before"
        )
        bt.setdefault("new_field", "test")
        with open(bt.filepath, "r") as f:
            reloaded_bt = bt.from_yaml(f)
        os.remove(bt.filepath)
        self.assertEqual(reloaded_bt["new_field"], "test")
        self.assertEqual(reloaded_bt, bt)

    def test_yaml_sync_between_objects(self):
        """Updating a Beamtime updates Experiment(s) and Sample(s)"""
        "that refer to it"

        self.bt["new_bt_field"] = "test"
        # Experiment and Sample should be automatically synced.
        for el in self.bt.samples:
            with open(el.filepath, "r") as f:
                reloaded_sa = el.from_yaml(f)
            self.assertTrue("new_bt_field" in reloaded_sa)

    @staticmethod
    def test_chaining():
        """All contents of Beamtime and Experiment should propagate into
        Sample."""
        bt = Beamtime("Simon", 123, [], wavelength=0.1828, custom1="A")
        sa_dict = {"sample_name": "Ni", "sample_composition": {"Ni": 1}}
        sa = Sample(bt, sa_dict)
        for k, v in bt.items():
            assert sa[k] == bt[k]

    def test_load_beamtime(self):
        bt = Beamtime("Simon", 123, [], wavelength=0.1828, custom1="A")
        sa_dict = {"sample_name": "Ni", "sample_composition": {"Ni": 1}}
        sa = Sample(bt, sa_dict)

        bt2 = load_beamtime()
        self.assertEqual(bt2, bt)
        self.assertEqual(list(bt2.samples.values())[0], sa)

    @staticmethod
    def test_list_bkg_smoke():
        bt = Beamtime("Simon", 123, [], wavelength=0.1828, custom1="A")
        bt.list_bkg()

    def test_min_exposure_time(self):
        bt = Beamtime("Simon", 123, [], wavelength=0.1828, custom1="A")
        # shorter than acq time -> ValueError
        glbl["frame_acq_time"] = 0.5
        print("frame acq time = {}".format(glbl["frame_acq_time"]))
        # exposure as arg
        self.assertRaises(ValueError, lambda: ScanPlan(bt, ct, 0.2))
        # exposure as kwarg
        self.assertRaises(ValueError, lambda: ScanPlan(bt, ct, exposure=0.2))
        # proper frame acq time -> pass
        glbl["frame_acq_time"] = 0.1
        ScanPlan(bt, ct, 0.2)
        # test with xrun
        xrun = CustomizedRunEngine(bt)
        xrun({}, ScanPlan(bt, ct, 0.2))  # safe, should pass
        glbl["frame_acq_time"] = 0.5
        self.assertRaises(ValueError, lambda: xrun({}, ScanPlan(bt, ct, 0.2)))
        glbl["frame_acq_time"] = 0.1  # reset after test
