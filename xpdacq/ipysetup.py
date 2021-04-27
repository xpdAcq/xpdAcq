"""Set up the objects ipython profile."""
import databroker
import typing as tp
from ophyd.sim import SynAxis, SynSignalWithRegistry, SynSignalRO
from xpdconf.conf import XPD_SHUTTER_CONF
from xpdsim.movers import SimFilterBank

from .beamtime import Beamtime
from .beamtimeSetup import start_xpdacq
from .plans import XrayBasicPlans
from .xpdacq import CustomizedRunEngine
from .xpdacq_conf import GlblYamlDict
from .xpdacq_conf import _load_beamline_config
from .xpdacq_conf import configure_device, _reload_glbl, _set_glbl


def ipysetup(
    *,
    area_det: SynSignalWithRegistry,
    shutter: SynAxis,
    temp_controller: SynAxis,
    filter_bank: SimFilterBank,
    ring_current: SynSignalRO,
    db: databroker.v1.Broker,
    glbl_yaml: str = None,
    blconfig_yaml: str = None,
    test: bool = False
) -> tp.Tuple[GlblYamlDict, Beamtime, CustomizedRunEngine, XrayBasicPlans]:
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
    glbl : dict
        A dictionary of the global configuration for this beam time. The variable is `~xpdacq.glbl.glbl`.

    bt : Beamtime
        An interface to create, read and update the plans, samples and beam time information.

    xrun : CustomizedRunEngine
        A customized bluesky run engine to run the plans.

    xbp : XrayBasicPlans
        The XrayBasicPlans object.
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
    xrun = CustomizedRunEngine(bt)
    xrun.md["beamline_id"] = glbl.get("beamline_id", "")
    xrun.md["group"] = glbl.get("group", "")
    xrun.md["facility"] = glbl.get("facility", "")
    if blconfig_yaml:
        xrun.md["beamline_config"] = _load_beamline_config(blconfig_yaml, test=test)
    # create the xray basic plans
    xbp = XrayBasicPlans(shutter=shutter, shutter_open=XPD_SHUTTER_CONF["open"],
                         shutter_close=XPD_SHUTTER_CONF["close"], db=db)
    return glbl, bt, xrun, xbp
