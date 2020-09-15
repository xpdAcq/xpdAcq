import pytest
from xpdacq.ipysetup import ipysetup
from xpdsim import xpd_pe1c, shctl1, cs700, ring_current, fb
from databroker import Broker


@pytest.mark.parametrize(
    "glbl_yaml", [None]
)
def test_ipysetup(glbl_yaml, capfd, beamline_config_file):
    with capfd.disabled():
        db = Broker.named("temp")
        from xpdacq.glbl import glbl
        glbl, bt, xrun = ipysetup(
            area_det=xpd_pe1c,
            shutter=shctl1,
            temp_controller=cs700,
            filter_bank=fb,
            ring_current=ring_current,
            db=db,
            glbl_yaml=glbl_yaml,
            blconfig_yaml=beamline_config_file,
            test=True
        )
    assert glbl
    assert not bt
    assert xrun
