import shutil
import pytest
from pathlib import Path

from databroker.v2 import temp
from pkg_resources import resource_filename
from xpdacq.ipysetup import (CalibPreprocessor, UserInterface,
                             _set_calib_preprocessor)
from xpdacq.simulators import PerkinElmerDetector, Stage
from xpdsim import cs700, fb, ring_current, shctl1, xpd_pe1c

_PONI_FILFE = Path(resource_filename("xpdacq", "tests/Ni_poni_file.poni"))


@pytest.mark.skip
def test_ipysetup(beamline_config_file):
    db = temp()
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
    assert ui is not None


@pytest.mark.skip
def test__set_calib_preprocessor(tmp_path: Path):
    det = PerkinElmerDetector(name="det")
    det_z = Stage(name="det_stage").z
    poni_file = tmp_path.joinpath(_PONI_FILFE.name)
    shutil.copy(_PONI_FILFE, poni_file)
    dct = {
        "config_base": str(poni_file.parent),
        "calib_config_name": poni_file.name
    }
    # case 1
    cpp1 = CalibPreprocessor(det)
    _set_calib_preprocessor(cpp1, dct, None)
    assert cpp1._cache
    first = next(iter(cpp1._cache.keys()))
    assert dict(first) == dict()
    # case 2
    cpp2 = CalibPreprocessor(det)
    _set_calib_preprocessor(cpp2, dct, det_z)
    assert cpp2._cache
    first = next(iter(cpp2._cache.keys()))
    assert dict(first) == {det_z.name: det_z.get()}
