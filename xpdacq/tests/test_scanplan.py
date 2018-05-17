import os
import itertools
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from xpdacq.xpdacq_conf import xpd_configuration, glbl_dict
from xpdconf.conf import XPD_SHUTTER_CONF
from xpdacq.beamtime import tseries


def _verify_tseries_message(msgs):
    # test message stream first --> ``open`` shutter before ``trigger``
    # and ``close`` shutter after ``read``
    # expected message stream:  set -> wait -> checkpoint -> trigger
    # expected message stream:  save -> set -> wait -> checkpoint
    trigger_msg_pos = [i for i, x in enumerate(msgs) if
                       x.command=='trigger']
    print([msgs[ind-3].args for ind in trigger_msg_pos])
    assert all([msgs[ind-3].command=='set' for ind in trigger_msg_pos])
    assert all([msgs[ind-3].args[0]==XPD_SHUTTER_CONF['open']\
        for ind in trigger_msg_pos])  # first arg
    assert all([msgs[ind-1].command=='checkpoint' for ind in trigger_msg_pos])
    save_msg_pos = [i for i, x in enumerate(msgs) if
                    x.command=='save']
    print([msgs[ind+3].command for ind in save_msg_pos])
    assert all([msgs[ind+1].command=='set' for ind in save_msg_pos])
    assert all([msgs[ind+1].args[0]==XPD_SHUTTER_CONF['close']\
        for ind in save_msg_pos])  # first arg
    assert all([msgs[ind+3].command=='checkpoint' for ind in save_msg_pos])


def test_tseries_with_shutter_control_pureMsg(fresh_xrun):
    print(xpd_configuration)
    p = tseries([xpd_configuration['area_det']], 2, 0.5, 10, True)
    msgs = list(p)
    _verify_tseries_message(msgs)


def test_tseries_with_shutter_control_xrun(fresh_xrun, glbl):
    print(xpd_configuration)
    xrun = fresh_xrun
    glbl['shutter_control'] = False  # no auto-dark for a clean test
    xrun_msgs = []
    xrun.msg_hook = lambda x: xrun_msgs.append(x)
    p = tseries([xpd_configuration['area_det']], 2, 0.5, 10, True)
    xrun({}, p)
    _verify_tseries_message(xrun_msgs)
    glbl['shutter_control'] = True  # reset to default
