import unittest
import asyncio
import os
import copy
import shutil
import time
import yaml
import uuid
import warnings
from pprint import pprint
from xpdacq.glbl import glbl
from xpdacq.beamtime import _nstep
from xpdacq.beamtime import *
from xpdacq.tools import xpdAcqException
from xpdacq.utils import import_sample_info
from xpdacq.xpdacq_conf import (
    configure_device,
    XPDACQ_MD_VERSION,
    _load_beamline_config,
)
from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
from xpdacq.xpdacq import (
    _validate_dark,
    CustomizedRunEngine,
    _auto_load_calibration_file,
    set_beamdump_suspender,
)
from xpdacq.simulation import pe1c, cs700, shctl1, db, fb
import ophyd
from bluesky import Msg
import bluesky.examples as be
from bluesky.callbacks import collector

from pkg_resources import resource_filename as rs_fn
from xpdsim import dexela

pytest_dir = rs_fn("xpdacq", "tests/")


class xrunTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl["base"]
        self.home_dir = glbl["home_dir"]
        self.config_dir = glbl["xpdconfig"]
        self.PI_name = "Billinge "
        # must be 30000 for proper load of config yaml => don't change
        self.saf_num = 300000
        self.wavelength = 0.1812
        self.experimenters = [
            ("van der Banerjee", "S0ham", 1),
            ("Terban ", " Max", 2),
        ]
        # make xpdUser dir. That is required for simulation
        os.makedirs(self.home_dir, exist_ok=True)
        # set simulation objects
        configure_device(
            area_det=pe1c,
            temp_controller=cs700,
            shutter=shctl1,
            db=db,
            filter_bank=fb,
        )
        os.makedirs(glbl["xpdconfig"], exist_ok=True)
        pytest_dir = rs_fn("xpdacq", "tests/")
        config = "XPD_beamline_config.yml"
        configsrc = os.path.join(pytest_dir, config)
        shutil.copyfile(configsrc, glbl["blconfig_path"])
        self.bt = _start_beamtime(
            self.PI_name,
            self.saf_num,
            self.experimenters,
            wavelength=self.wavelength,
            test=True,
        )
        xlf = "300000_sample.xlsx"
        src = os.path.join(os.path.dirname(__file__), xlf)
        shutil.copyfile(src, os.path.join(glbl["import_dir"], xlf))
        import_sample_info(self.saf_num, self.bt)
        self.xrun = CustomizedRunEngine({})
        self.xrun.beamtime = self.bt
        # link mds
        self.xrun.subscribe(xpd_configuration["db"].insert, "all")
        # grad init_exp_hash_uid
        self.init_exp_hash_uid = glbl["exp_hash_uid"]

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, "xpdConfig")):
            shutil.rmtree(os.path.join(self.base_dir, "xpdConfig"))
        if os.path.isdir(os.path.join(self.base_dir, "pe2_data")):
            shutil.rmtree(os.path.join(self.base_dir, "pe2_data"))

    def test_validate_dark(self):
        """ test login in this function """
        # no dark_dict_list
        glbl["_dark_dict_list"] = []
        rv = _validate_dark()
        assert rv is None
        # initiate dark_dict_list
        dark_dict_list = []
        now = time.time()
        # configure area detector
        xpd_configuration["area_det"].cam.acquire_time.put(0.1)
        xpd_configuration["area_det"].images_per_set.put(5)
        acq_time = xpd_configuration["area_det"].cam.acquire_time.get()
        num_frame = xpd_configuration["area_det"].images_per_set.get()
        light_cnt_time = acq_time * num_frame
        # case1: adjust exposure time
        for i in range(5):
            dark_dict_list.append(
                {
                    "uid": str(uuid.uuid4()),
                    "exposure": (i + 1) * 0.1,
                    "timestamp": now,
                    "acq_time": acq_time,
                }
            )
        glbl["_dark_dict_list"] = dark_dict_list
        rv = _validate_dark(glbl["dk_window"])
        correct_set = sorted(
            [
                el
                for el in dark_dict_list
                if abs(el["exposure"] - light_cnt_time) < acq_time
            ],
            key=lambda x: x["exposure"],
        )[0]
        print(dark_dict_list)
        print("correct_set = {}".format(correct_set))
        assert rv == correct_set.get("uid")

        # case2: adjust expire time
        dark_dict_list = []
        for i in range(5):
            dark_dict_list.append(
                {
                    "uid": str(uuid.uuid4()),
                    "exposure": light_cnt_time,
                    "timestamp": now - (i + 1) * 60,
                    "acq_time": acq_time,
                }
            )
        glbl["_dark_dict_list"] = dark_dict_list
        # large window -> still find the best (freshest) one
        rv = _validate_dark()
        assert rv == dark_dict_list[0].get("uid")
        # small window -> find None
        rv = _validate_dark(0.1)
        assert rv is None
        # medium window -> find the first one as it's within 1 min window
        rv = _validate_dark(1.5)
        assert rv == dark_dict_list[0].get("uid")

        # case3: adjust acqtime
        dark_dict_list = []
        for i in range(5):
            dark_dict_list.append(
                {
                    "uid": str(uuid.uuid4()),
                    "exposure": light_cnt_time,
                    "timestamp": now,
                    "acq_time": acq_time * (i + 1),
                }
            )
        glbl["_dark_dict_list"] = dark_dict_list
        # leave for future debug
        # print("dark_dict_list = {}"
        #      .format([(el.get('exposure'),
        #                el.get('timestamp'),
        #                el.get('uid'),
        #                el.get('acq_time'))for el in
        #                glbl['_dark_dict_list']]))
        rv = _validate_dark()
        assert rv == dark_dict_list[0].get("uid")

        # case4: with real xrun
        if glbl["_dark_dict_list"]:
            glbl["_dark_dict_list"] = []
        xrun_uid = self.xrun({}, 0)
        print(xrun_uid)
        assert len(xrun_uid) == 2  # first one is auto_dark
        dark_uid = _validate_dark()
        assert xrun_uid[0] == dark_uid
        # test sc_dark_field_uid
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun(0, 0)
        open_run = [el.kwargs for el in msg_list if el.command == "open_run"][
            0
        ]
        assert dark_uid == open_run["sc_dk_field_uid"]
        # no auto-dark
        glbl["auto_dark"] = False
        new_xrun_uid = self.xrun(0, 0)
        assert len(new_xrun_uid) == 1  # no dark frame
        assert glbl["_dark_dict_list"][-1]["uid"] == dark_uid  # no update

    def test_auto_load_calibration(self):
        # no config file in xpdUser/config_base
        auto_calibration_md_dict = _auto_load_calibration_file()
        assert auto_calibration_md_dict is None
        # one config file in xpdUser/config_base:
        cfg_f_name = glbl["calib_config_name"]
        cfg_src = os.path.join(pytest_dir, cfg_f_name)
        cfg_dst = os.path.join(glbl["config_base"], cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        with open(cfg_dst) as f:
            config_from_file = yaml.unsafe_load(f)
        reload_calibration_md_dict = _auto_load_calibration_file()
        # test with xrun : auto_load_calib = True -> full calib_md
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        glbl["auto_load_calib"] = True
        xrun_uid = self.xrun(0, 0)
        open_run = [el.kwargs for el in msg_list if el.command == "open_run"][
            0
        ]
        # equality
        self.assertTrue("calibration_md" in open_run)
        self.assertEqual(
            open_run["calibration_md"], reload_calibration_md_dict
        )
        # specific info encoded in test file
        self.assertEqual(open_run["calibration_md"]["is_pytest"], True)

        # test with xrun : auto_load_calib = False -> nothing happpen
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        glbl["auto_load_calib"] = False
        xrun_uid = self.xrun(0, 0)
        open_run = [el.kwargs for el in msg_list if el.command == "open_run"][
            0
        ]
        self.assertFalse("calibration_md" in open_run)

    def test_xrun_with_xpdAcqPlans(self):
        exp = 5
        # test with ct
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, ct, exp))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        self.assertEqual(open_run["sp_type"], "ct")
        self.assertEqual(open_run["sp_requested_exposure"], exp)
        # test with Tramp
        Tstart, Tstop, Tstep = 300, 200, 10
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        traj_list = []  # courtesy of bluesky test
        temp_controller = xpd_configuration["temp_controller"]
        callback = collector(temp_controller.readback.name, traj_list)
        self.xrun(
            {},
            ScanPlan(self.bt, Tramp, exp, Tstart, Tstop, Tstep),
            subs={"event": callback},
        )
        # verify trajectory
        Num, diff = _nstep(Tstart, Tstop, Tstep)
        expected_traj = np.linspace(Tstart, Tstop, Num)
        assert np.all(traj_list == expected_traj)
        # verify md
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        self.assertEqual(open_run["sp_type"], "Tramp")
        self.assertEqual(open_run["sp_requested_exposure"], exp)
        self.assertEqual(open_run["sp_startingT"], Tstart)
        self.assertEqual(open_run["sp_endingT"], Tstop)
        self.assertEqual(open_run["sp_requested_Tstep"], Tstep)
        # test with tseries
        delay, num = 0.1, 5
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, tseries, exp, delay, num))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        self.assertEqual(open_run["sp_type"], "tseries")
        self.assertEqual(open_run["sp_requested_exposure"], exp)
        self.assertEqual(open_run["sp_requested_delay"], delay)
        self.assertEqual(open_run["sp_requested_num"], num)
        # test with Tlist
        T_list = [300, 256, 128]
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        traj_list = []  # courtesy of bluesky test
        temp_controller = xpd_configuration["temp_controller"]
        callback = collector(temp_controller.readback.name, traj_list)
        self.xrun.msg_hook = msg_rv
        self.xrun(
            {}, ScanPlan(self.bt, Tlist, exp, T_list), subs={"event": callback}
        )
        # verify trajectory
        assert T_list == traj_list
        # verify md
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        self.assertEqual(open_run["sp_type"], "Tlist")
        self.assertEqual(open_run["sp_requested_exposure"], exp)
        self.assertEqual(open_run["sp_T_list"], T_list)

    def test_shutter_step(self):
        # test with Tramp
        shutter = xpd_configuration["shutter"]
        temp_controller = xpd_configuration["temp_controller"]
        exp, Tstart, Tstop, Tstep = 5, 300, 200, 10
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, Tramp, exp, Tstart, Tstop, Tstep))
        set_msg_list = [msg for msg in msg_list if msg.command == "set"]
        set_msgs = iter(set_msg_list)
        while True:
            try:
                set_msg = next(set_msgs)
                if set_msg.obj.name == temp_controller.name:
                    # after set the temp_controller, must be:
                    # open shutter -> read -> close
                    open_msg = next(set_msgs)
                    assert open_msg.obj.name == shutter.name
                    assert len(open_msg.args) == 1
                    assert open_msg.args[0] == 60  # open shutter first
                    close_msg = next(set_msgs)
                    assert close_msg.obj.name == shutter.name
                    assert len(close_msg.args) == 1
                    assert close_msg.args[0] == 0  # close then move
            except StopIteration:
                print("stop")
                break

    def test_set_beamdump_suspender(self):
        # operate at full current
        sig = ophyd.Signal(name="ring_current")
        xpd_configuration["ring_current"] = sig
        set_beamdump_suspender(self.xrun, wait_time=0.1)
        sig.put(200)
        self.xrun({}, ScanPlan(self.bt, ct, .1))
        # operate at low current, test user warnning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # trigger warning
            sig.put(30)  # low current
            set_beamdump_suspender(self.xrun, wait_time=0.1)
            # check warning
            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)

    def test_xpdmd_insert(self):
        key = "xpdacq_md_version"
        val = XPDACQ_MD_VERSION
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        assert key in open_run
        assert open_run[key] == val

    def test_analysis_stage_insert(self):
        key = "analysis_stage"
        val = "raw"
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        assert key in open_run
        assert open_run[key] == val

    def test_calibration_client_server_md_insert(self):
        server_val = self.init_exp_hash_uid
        client_key = "detector_calibration_client_uid"
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        glbl["auto_load_calib"] = True
        assert glbl["auto_load_calib"] == True
        # calibration hasn't been run -> still receive client uid
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        assert client_key in open_run
        assert open_run[client_key] == server_val
        # attach calib md to glbl and verify injection
        cfg_f_name = glbl["calib_config_name"]
        cfg_src = os.path.join(pytest_dir, cfg_f_name)
        cfg_dst = os.path.join(glbl["config_base"], cfg_f_name)
        shutil.copy(cfg_src, cfg_dst)
        with open(cfg_dst) as f:
            config_from_file = yaml.unsafe_load(f)
        glbl["calib_config_dict"] = config_from_file
        msg_list = []

        def msg_rv(msg):
            msg_list.append(msg)

        self.xrun.msg_hook = msg_rv
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        open_run = [
            el.kwargs for el in msg_list if el.command == "open_run"
        ].pop()
        assert client_key in open_run
        assert open_run[client_key] == server_val

    def test_facility_md(self):
        key_list = ["owner", "facility", "group"]
        for k in key_list:
            self.xrun.md[k] = glbl[k]
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        h = xpd_configuration["db"][-1]
        assert all(k in h.start for k in key_list)
        assert all(glbl[k] == h.start[k] for k in key_list)

    def test_double_scan(self):
        xpd_configuration["db"].prepare_hook = lambda name, doc: copy.deepcopy(
            doc
        )
        key_list = ["owner", "facility", "group"]
        for k in key_list:
            self.xrun.md[k] = glbl[k]
        uids = self.xrun(
            {"sample_name": "double_scan"},
            [ScanPlan(self.bt, ct, 1.0), ScanPlan(self.bt, ct, 1.0)],
        )
        hdrs = [xpd_configuration["db"][-1 * i] for i in [1, 2]]
        starts = [h["start"] for h in hdrs]
        for h in hdrs:
            assert "dark_frame" not in h["start"]
            assert h["start"]["uid"] in uids
            assert h["start"]["sample_name"] == "double_scan"

        pops = [
            "uid",
            "time",
            "sp_uid",
            "scan_id",
            # Due to [] () issues or timestamps
            "plan_args",
            "hints",
            "bt_experimenters",
        ]
        for p in ["uid", "time", "sp_uid", "scan_id"]:
            for s in starts[1:]:
                assert s[p] != starts[0][p]
        [s.pop(p) for s in starts for p in pops]
        for s in starts:
            assert s == starts[0]

    def test_load_beamline_config(self):
        # no beamline config -> raise
        if os.path.exists(glbl["blconfig_path"]):
            os.remove(glbl["blconfig_path"])
        with self.assertRaises(xpdAcqException):
            _load_beamline_config(glbl["blconfig_path"], test=True)
        # move files
        stem, fn = os.path.split(glbl["blconfig_path"])
        src = os.path.join(pytest_dir, fn)
        shutil.copyfile(src, glbl["blconfig_path"])
        beamline_config_dict = _load_beamline_config(
            glbl["blconfig_path"], test=True
        )
        assert "is_pytest" in beamline_config_dict
        # check md -> only is_pytest in template now
        self.xrun.md["beamline_config"] = beamline_config_dict
        self.xrun({}, ScanPlan(self.bt, ct, 1.0))
        hdr = xpd_configuration["db"][-1]
        print(beamline_config_dict)
        assert hdr.start["beamline_config"] == beamline_config_dict


def test_dexela(fresh_xrun):
    xpd_configuration['area_det'] = dexela
    xrun = fresh_xrun
    L = []
    xrun.subscribe(lambda *x: L.append(x))
    xrun({}, 0)
    assert L
