import pytest
from databroker import Broker
from xpdsim import xpd_pe1c, shctl1, cs700, ring_current, fb

from xpdacq.ipysetup import UserInterface


@pytest.mark.skip(reason="This will pause the session.")
def test_ipysetup(beamline_config_file):
    db = Broker.named("temp")
    ui = UserInterface(
        area_dets=[xpd_pe1c],
        det_zs=[None],
        shutter=shctl1,
        temp_controller=cs700,
        filter_bank=fb,
        ring_current=ring_current,
        db=db,
        blconfig_yaml=beamline_config_file,
        test=True
    )
    assert ui.glbl
    assert not ui.bt
    assert ui.xrun
    assert ui.xpd_configuration
