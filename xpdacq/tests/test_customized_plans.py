import xpdacq.beamtime as xbt
from xpdacq.beamtime import xpd_configuration
from xpdacq.simulators import WorkSpace


def test_configure_area_det():
    ws = WorkSpace()
    ws.RE(xbt.configure_area_det(ws.det, 5.0, 0.1))
    assert ws.det.cam.acquire_time.get() == 0.1
    assert ws.det.images_per_set.get() == 50


def test_ct():
    ws = WorkSpace()
    RE = ws.RE
    det = ws.det
    db = ws.db
    del ws
    xpd_configuration["area_det"] = det
    RE(xbt.ct([det], 0.1))
    assert db[-1]


def test_Tlist():
    ws = WorkSpace()
    RE = ws.RE
    det = ws.det
    db = ws.db
    eurotherm = ws.eurotherm
    del ws
    xpd_configuration["area_det"] = det
    xpd_configuration["temp_controller"] = eurotherm
    setpoints = [100.0, 200.0, 300.0]
    RE(xbt.Tlist([det], 0.1, setpoints))
    assert db[-1]


def test_Tramp():
    ws = WorkSpace()
    RE = ws.RE
    det = ws.det
    db = ws.db
    eurotherm = ws.eurotherm
    del ws
    xpd_configuration["area_det"] = det
    xpd_configuration["temp_controller"] = eurotherm
    setpoints = [100.0, 200.0, 300.0]
    RE(xbt.Tramp([det], 0.1, 100.0, 300.0, 100.0))
    assert db[-1]
