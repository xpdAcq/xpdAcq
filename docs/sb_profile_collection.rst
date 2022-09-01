.. _profile_collection:

Setup Profile Collection
------------------------

I will introduce how to set up the profile collection for the `IPython` session in this section. The profile collection is a folder of `*.py` files. These files will be executed in order when `bsui` is called. The `xrun` and other helper functions are added into the namespace by one of the `*.py` file. Its usual name is `999-load.py` or `94-load.py`.

This file has a big change at the version `1.1.0`. Thus, there is a if clause to determine how to create the python objects differently.

.. code-block:: python

    """XpdAcq Initializatoion

    Initialize the XpdAcq objects for xpdacq >= 1.1.0.
    This file will do the following changes to the name space:

        (1) create objects of `xrun`, `glbl` etc. using the UserInterface class in XpdAcq.
        (2) import helper functions for users from XpdAcq
        (3) change the home directory to `glbl['home']` or `glbl['base']`
        (4) disable the logging of pyFAI
    """
    import xpdacq

    xpdacq_version = tuple(map(int, xpdacq.__version__.split(".")))

    if xpdacq_version < (1, 1, 0):
        import os
        from xpdacq.xpdacq_conf import (glbl_dict, configure_device,
                                    _reload_glbl, _set_glbl,
                                    _load_beamline_config)

        # configure experiment device being used in current version
        if glbl_dict['is_simulation']:
            from xpdacq.simulation import (xpd_pe1c, db, cs700, shctl1,
                                        ring_current, fb)
            pe1c = xpd_pe1c # alias

        configure_device(area_det=pe1c, shutter=fs,
                        temp_controller=eurotherm, #changed from None to eurotherm on 3/22/19 - DPO
                        db=db,
                        filter_bank=fb,
                        ring_current=ring_current)

        # cache previous glbl state
        reload_glbl_dict = _reload_glbl()
        from xpdacq.glbl import glbl

        # reload beamtime
        from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                        _end_beamtime)

        bt = start_xpdacq()
        if bt is not None:
            print("INFO: Reload beamtime objects:\n{}\n".format(bt))
        if reload_glbl_dict is not None:
            _set_glbl(glbl, reload_glbl_dict)

        # import necessary modules
        from xpdacq.xpdacq import *
        from xpdacq.beamtime import *
        from xpdacq.utils import import_sample_info

        # instantiate xrun without beamtime, like bluesky setup
        xrun = CustomizedRunEngine(None)
        xrun.md['beamline_id'] = glbl['beamline_id']
        xrun.md['group'] = glbl['group']
        xrun.md['facility'] = glbl['facility']
        beamline_config = _load_beamline_config(glbl['blconfig_path'])
        xrun.md['beamline_config'] = beamline_config

        # insert header to db, either simulated or real
        xrun.subscribe(db.insert, 'all')

        if bt:
            xrun.beamtime = bt

        HOME_DIR = glbl['home']
        BASE_DIR = glbl['base']

        print('INFO: Initializing the XPD data acquisition environment\n')
        if os.path.isdir(HOME_DIR):
            os.chdir(HOME_DIR)
        else:
            os.chdir(BASE_DIR)

        # See https://github.com/silx-kit/pyFAI/issues/1399#issuecomment-694185304
        import logging
        logging.getLogger().addHandler(logging.NullHandler())

        from xpdacq.calib import *

        # analysis functions, only at beamline
        #from xpdan.data_reduction import *

        print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
        print('documentation at http://xpdacq.github.io/xpdacq\n')

    else:
        import os

        # Disable interactive logging of pyFAI
        # See https://github.com/silx-kit/pyFAI/issues/1399#issuecomment-694185304
        os.environ["PYFAI_NO_LOGGING"] = "1"

        from xpdacq.utils import import_userScriptsEtc, import_sample_info
        from xpdacq.beamtimeSetup import _start_beamtime, _end_beamtime
        from xpdacq.beamtime import ScanPlan, Sample, ct, Tramp, Tlist, tseries
        from xpdacq.ipysetup import UserInterface

        # Do all setup in the constructor of UserInterface
        # HOME directory will be changed to the one in glbl
        ui = UserInterface(
            area_dets=[pe1c],
            det_zs=[None],
            shutter=fs,
            temp_controller=eurotherm,
            filter_bank=fb,
            ring_current=ring_current,
            db=db
        )
        xrun = ui.xrun
        glbl = ui.glbl
        xpd_configuration = ui.xpd_configuration
        run_calibration = ui.run_calibration
        bt = ui.bt

        # Remove the variables that won't be used
        del UserInterface, ui

    # remove the uselss names
    del xpdacq_version


In the latest version, all python objects are created by the `UserInterface` class.

.. autoclass:: xpdacq.ipysetup.UserInterface
