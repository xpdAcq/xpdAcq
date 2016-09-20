.. _cheat_sheet:

Cheat Sheet
===========

Start a beamtime
----------------

.. code-block:: python

  bt = _start_beamtime(PI_last='Billinge', saf_num=300012,
                       experimenters = ['Emma', 'Watson', 'Tim', 'Liu', ‘Max’, ‘Terban’],
                       wavelength=0.184649)


.. note::

  * ``saf_num`` is the Safety Approval Form number to this beamtime

  * ``experimenters`` field is expected to be [‘first_name’, ‘last_name’, ‘fist_name’, ‘last_name’, ….]


link bt to prun
"""""""""""""""

.. code-block:: python

  prun.beamtime = bt


open a collection
"""""""""""""""""

.. code-block:: python

  open_collection('first_collection')

.. note::

  * ``collection_name`` ("first_collection" here) can be any name you want, as long as it is a string (in quotes)

  * Also you need to open a collection if you exit out and come back to ``ipython`` session


Running experiment
-------------------

calibration
"""""""""""

.. code-block:: python

  run_calibration(exposure=60)

.. note::
  * this function will run a calibration shot, for a short tutorial about calibration here :ref:`calib_manual`

  * default behavior assume **Ni** as the calibrant and default ``exposure`` time is 60 seconds.

  * use ``run_calibration?`` to find out more information


setup ``Sample`` objects
""""""""""""""""""""""""

Example:

.. code-block:: python

  Sample(bt, {'sample_name':'Ni', 'sample_composition':{'Ni':1}} )
  Sample(bt, {'sample_name':'TiO2', 'sample_composition':{'Ti':1, 'O':2}})

.. note::

  * ``sample_name`` and ``sample_composition`` are both required.

  * ``sample_name`` needs to be a string and ``sample_composition`` needs to be a dictionary, namely in a {`key`: `value`} form.

  * for the richness of your metadata, we encourage you to use spreadsheet to enter your metadata. Please see link here **FIXME**



setup ``ScanPlan`` objects
""""""""""""""""""""""""""

Example:

======================================= ===================================================================================
command
======================================= ===================================================================================
``ScanPlan(bt, ct, 5)``                  a count scan for 5s

``ScanPlan(bt, tseries, 5, 50, 15)``     time series with 5s count time, 50s delay and 5 repeats

``ScanPlan(bt, Tramp, 5, 300, 200, 5)``  temperature series with 5s count time, starting from 300k to 200k with 5k per step
======================================= ===================================================================================

list objects by categories
"""""""""""""""""""""""""""

.. code-block:: python

  bt.list()
  ScanPlans:
  0: 'ct_5'
  1: 'Tramp_5_300_200_5'
  2: 'tseries_5_50_15'

  Samples:
  0: Ni
  1: TiO2


interrogating metadata in objects
""""""""""""""""""""""""""""""""""

.. code-block:: python

  bt.samples[1].md
  bt.scanplans [5].md

running scan with acquire objects
""""""""""""""""""""""""""""""""""

*on this sample, run this scan plan*

**production run engine**

.. code-block:: python

  prun(bt.samples[2],  bt.scanplan[5]) # indexing object explicitly

  prun(2,5)  # inexplicit give ``Sample`` and ``ScanPlan`` index

.. note::

  remember to change the index according to your bt.list() result!


saving image from your scans
""""""""""""""""""""""""""""

**last scan:**

.. code-block:: python

  save_last_tiff()

**last n headers to now:**

.. code-block:: python

  h = db[-n:]
  save_tiff(h)

**p headers away from now:**

.. code-block:: python

  h = db[-p]
  save_tiff(h)

end a beamtime
""""""""""""""

.. code-block:: python

  _end_beamtime()

.. note::

  * After running this command, directories under ``xpdUser`` will be archived and backed up remotely.

  * Only run this when you are done with your beamtime.

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

Checklist
---------

The instrument scientist (IS) should have set up your beamtime hardware and software
for you.  Let's check if it is the case.

1. Activate the XPD data acquisition environment:

  * In a terminal look to see if it is already activated.  If it is, you should see ``(collection-dev)`` at the beginning of the line.

  .. code-block:: none

    (collection-dev)xf28id1@xf28id1-ws2:~$


2. Check that the Perkin Elmer detector is correctly set up.

  * Look at the Perkin Elmer screen on the CSS and make sure that ``Acquire`` mode has been enabled. If Acquire mode is enabled, it should show system information ``Collecting`` in yellow color. If it hasn't been activated, please click ``start`` button.

  .. image:: /cropped_pe1c_ioc.png
    :width: 300px
    :align: center
    :height: 200px

  * Type ``glbl.area_det`` and return.  It should return:

   .. code-block:: python

     In [1]: glbl.area_det
     Out[1]: PerkinElmerContinuous(prefix='XF:28IDC-ES:1{Det:PE1}', name='pe1', read_attrs=['tiff', 'stats1'],
                                   configuration_attrs=['images_per_set', 'number_of_sets'],
                                   monitor_attrs=[])
