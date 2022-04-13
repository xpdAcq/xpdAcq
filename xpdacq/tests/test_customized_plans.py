import xpdacq.beamtime as xbt
from xpdacq.beamtime import xpd_configuration
from xpdacq.simulators import WorkSpace


def test_configure_area_det():
    ws = WorkSpace()
    ws.RE(xbt.configure_area_det(ws.det, 5., 0.1))
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
    key = "{}_image".format(det.name)
    data = list(db[-1].data(key))
    assert len(data) == 1


def test_Tlist():
    ws = WorkSpace()
    RE = ws.RE
    det = ws.det
    db = ws.db
    eurotherm = ws.eurotherm
    del ws
    xpd_configuration["area_det"] = det
    xpd_configuration["temp_controller"] = eurotherm
    setpoints = [100., 200., 300.]
    RE(xbt.Tlist([det], 0.1, setpoints))
    key = eurotherm.name
    measured = list(db[-1].data(key))
    assert measured == setpoints


def test_Tramp():
    ws = WorkSpace()
    RE = ws.RE
    det = ws.det
    db = ws.db
    eurotherm = ws.eurotherm
    del ws
    xpd_configuration["area_det"] = det
    xpd_configuration["temp_controller"] = eurotherm
    setpoints = [100., 200., 300.]
    RE(xbt.Tramp([det], 0.1, 100., 300., 100.))
    key = eurotherm.name
    measured = list(db[-1].data(key))
    assert measured == setpoints
