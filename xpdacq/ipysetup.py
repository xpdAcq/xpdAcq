"""Set up the objects ipython profile."""
import typing as tp
from databroker import Broker
from ophyd.sim import SynAxis, SynSignalWithRegistry, SynSignalRO
from xpdsim.movers import SimFilterBank

from .beamtime import Beamtime
from .beamtimeSetup import start_xpdacq
from .xpdacq import CustomizedRunEngine
from .xpdacq_conf import GlblYamlDict
from .xpdacq_conf import _load_beamline_config
from .xpdacq_conf import configure_device, _reload_glbl, _set_glbl


def ipysetup(
    area_det: SynSignalWithRegistry,
    shutter: SynAxis,
    temp_controller: SynAxis,
    filter_bank: SimFilterBank,
    ring_current: SynSignalRO,
    db: Broker,
    glbl_yaml: str = None,
    blconfig_yaml: str = None,
    test: bool = False
) -> tp.Tuple[GlblYamlDict, Beamtime, CustomizedRunEngine]:
    """Set up the beamtime, run engine and global configuration.

    Parameters
    ----------
    area_det :
        Area detector, like "pe1c".

    shutter :
        Shutter control, like "shctl1".

    temp_controller :
        Temperature control, like "cs700".

    filter_bank :
        The filter bank, like "fb".

    ring_current :
        The ring current reader, like "ring_current".

    db :
        The data broker.

    glbl_yaml :
        The global configuration for the beam time in a yaml file.
        If None, use the 'glbl_yaml_path' specified in the `xpdacq.xpdacq_conf.glbl_dict`.
        Default None.

    blconfig_yaml :
        The beamline configuratino yaml file. If None, use glbl["blconfig_path"].

    test :
        If true, use test mode (for developers).

    Returns
    -------
    glbl :
        A dictionary of the global configuration for this beam time. The variable is `~xpdacq.glbl.glbl`.

    bt :
        An interface to create, read and update the plans, samples and beam time information.

    xrun :
        A customized bluesky run engine to run the plans.
    """
    # configure devices
    configure_device(
        area_det=area_det,
        shutter=shutter,
        temp_controller=temp_controller,
        filter_bank=filter_bank,
        ring_current=ring_current,
        db=db
    )
    # reload glbl
    from xpdacq.glbl import glbl
    _glbl = _reload_glbl(glbl_yaml)
    if _glbl:
        _set_glbl(glbl, _glbl)
    # load beamtime
    bt = start_xpdacq()
    if bt:
        print("INFO: Reload beamtime objects:\n{}\n".format(bt))
    else:
        print("INFO: No Beamtime object.")
    # instantiate xrun without beamtime, like bluesky setup
    xrun = CustomizedRunEngine(None)
    xrun.md["beamline_id"] = glbl["beamline_id"]
    xrun.md["group"] = glbl["group"]
    xrun.md["facility"] = glbl["facility"]
    if not blconfig_yaml:
        blconfig_yaml = glbl["blconfig_path"]
    xrun.md["beamline_config"] = _load_beamline_config(blconfig_yaml, test=test)
    # insert header to db, either simulated or real
    xrun.subscribe(db.v1.insert)
    if bt:
        xrun.beamtime = bt
    return glbl, bt, xrun
