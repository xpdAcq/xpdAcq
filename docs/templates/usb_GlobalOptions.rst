.. _usb_GlobalOptions:

xpdAcq Configuration
--------------------

``xpdAcq`` uses ``glbl`` and ``xpd_configuration`` to controls the overall behavior of the beamtime.
All of the values of the ``glbl`` and ``xpd_configuration`` have reasonable default values, but these can be interrogated and overwritten.

Funtionality related options
""""""""""""""""""""""""""""
  Functionality related options are managed by ``glbl`` and you can 
  interrogate the default values by typing:
    
  .. code-block:: python

    glbl

  You can also change them if needed. Here are few possible scenarios:

  **No automated dark collection logic at all:**

  .. code-block:: python

    glbl['auto_dark'] = False
    glbl['shutter_control'] = False

  **Want a fresh dark frame every time ``xrun`` is triggered:**

  .. code-block:: python

    glbl['dk_window'] = 0.1 # dark window is 0.1 min = 6 secs


  **Want a 0.2s exposure time per frame instead of 0.1s:**

  .. code-block:: python

    glbl['frame_acq_time'] = 0.2

  changes made to ``glbl`` will be recovered after coming back to ``ipython`` session.
  So you don't have to redo the changes from time to time.



.. _usb_DeviceOptions:

Device-related options
""""""""""""""""""""""
    Device related configurations are stored in ``xpd_configuration``
    and you can interrogate the default values by typing:
    
    .. code-block:: python

      xpd_configuration
    
    You may also change the defaults:

    **Want to run temperature ramp with different device:**

    .. code-block:: python

      xpd_configuration['temp_controller'] = eurotherm

    **Want to use alternative shutter:**
    
    .. code-block:: python

      xpd_configuration['shutter'] = shctl2

    All of the changes applied to ``xpd_configuration`` only lives
    within one ``ipython`` session. So if you exit out the terminal and 
    come back, remember to repeat the configuration step *again*.

    .. note::

      desired objects (``eurotherm`` and ``shctl2`` above, for example) should be properly *configured*. How to properly configure a device is beyond the scope of this website, if you have specific requests, please contact beamline staff for more details.
