
Global options
--------------

``glbl`` class has several attributes that control the overall behavior of ``xpdacq`` software.

Automated dark related:

==================== =======================================================================
attributes
==================== =======================================================================
``dk_window``        means desired dark window in minutes, default is 3000
``auto_dark``        corresponds to logic of automated dark collection, default is ``True``.
==================== =======================================================================


Automated calibration parameter injection:

==================== =======================================================================
attributes
==================== =======================================================================
``auto_load_calib``      logic of automated loading calibration prameters, default is ``True``.
==================== =======================================================================


Configuration on experimental instruments:

==================== ====================================================================
attributes
==================== ====================================================================
``shutter_control``  control fast shutter or not, default is True
``frame_acq_time``   exposure per frame in seconds, default is 0.1s
``temp_controller``  object name of desired temperature controller, default is ``cs700``
``shutter``          object name of desired shutter, default is ``shctl1``
==================== ====================================================================


Possible scenarios:
"""""""""""""""""""

    **No automated dark collection logic at all:**

    .. code-block:: python

      glbl.auto_dark = False
      glbl.shutter_control = False

    **Want a fresh dark frame every time ``prun`` is triggered:**

    .. code-block:: python

      glbl.dk_window = 0.001 # dark window is 0.001 min = 0.06 secs


    **Want a 0.2 exposure time per frame instead of 0.1s:**

    .. code-block:: python

      glbl.frame_acq_time = 0.2

    **Want to run temperature ramp with different device and use alternative shutter:**

    .. code-block:: python

      glbl.temp_controller = eurotherm
      glbl.shutter = shctl2

    .. note::

      desired objects should be properly *configured*. For more details, please contact beamline staff.
