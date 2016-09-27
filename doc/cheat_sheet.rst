.. _cheat_sheet:

Cheat Sheet
===========

This cheat-sheet contains no explanation of how the ``xpdAcq`` software works.
to understand this, please go :ref:`qs` or :ref:`xpdu`

Please use this page as a reminder of the workflow and to copy & paste code snippets into your  
active ``collection-dev`` ipython environment (then hit return).

Check your data collection environment is correctly set up
----------------------------------------------------------

.. code-block:: python

  bt.md
  
should return a list of metadata about your experiment, such as PI last name.  If not
please get your beamtime environment set up by the instrument scientist before proceeding.

Set up your experiment
----------------------

1. calibration
""""""""""""""
run this first, then run it again each time the geometry of your measurement changes.  Place the
Ni calibrant at the sample position, type

.. code-block:: python

  run_calibration(exposure=60) # assume calibrant is Ni

and follow the instructions in :ref:`calib_manual`

.. autofunction::

  xpdacq.calib.run_calibration

2. set up ``Sample`` objects
""""""""""""""""""""""""""""

Your sample information should be loaded in an excel spreadsheet.  Type

.. code-block:: python

  import_sample(saf_num=300064, bt)

and follow instructions FIXME: I don't know the workflow...

Additional samples may be added by adding samples to the excel file and rerunning.

More information here :ref:`???`

3. set up ``ScanPlan`` objects
""""""""""""""""""""""""""""""

======================================= ===================================================================================
command
======================================= ===================================================================================
``ScanPlan(bt, ct, 5)``                  a count scan for 5s

``ScanPlan(bt, tseries, 5, 50, 15)``     time series with 5s count time, 50s delay and 15 repeats

``ScanPlan(bt, Tramp, 5, 300, 200, 5)``  temperature series with 5s count time, starting from 300k to 200k with 5k per step
======================================= ===================================================================================

More information here :ref:`???`

4. set up the file for saving output
""""""""""""""""""""""""""""""""""""
FIXME

5. list objects by categories
"""""""""""""""""""""""""""""

.. code-block:: python

  in[1]: bt.list()
  Out[1]:

  ScanPlans:
  0: 'ct_5'
  1: 'Tramp_5_300_200_5'
  2: 'tseries_5_50_15'

  Samples:
  0: Ni
  1: TiO2


6. interrogate metadata in objects
""""""""""""""""""""""""""""""""""

.. code-block:: python

  bt.samples[1].md        # returns metadata for item 1 in Sample list, i.e., TiO2
  bt.scanplans[5].md      # returns metadata for item 5 in scanplans list

Run your experiment
-------------------

1. A scan is a scanplan executed on a sample
""""""""""""""""""""""""""""""""""""""""""""

**on this sample run this scanplan**

.. code-block:: python

  prun(bt.samples[2],bt.scanplan[5]) # referencing objects explicitly
  prun(2,5)                          # inexplicit: give reference to ``Sample`` and ``ScanPlan`` 
                                     # index from the ``bt`` list

other scan-types are available

.. code-block:: python

  background(3,8)             # tags the run as a background scan
  setupscan(2,5)              # tags the run as a setup.  It will be saved 
                              # but easy to separate from your production runs later 
  dryrun(2,5)                 # scan is not run, but returns some information about scan

2. Interrupt your scan
""""""""""""""""""""""

table from `original package <http://nsls-ii.github.io/bluesky/state-machine.html#interactive-pause-summary>`_

a) Interactively Interrupt Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

======================= ===========
Command                 Outcome
======================= ===========
Ctrl+C                  Pause soon
Ctrl+C twice            Pause now
Ctrl+C three times fast (Shortcut) Pause now and abort
======================= ===========

b) Recovering from the paused state caused by an interrupt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

============== ===========
Command        Outcome
============== ===========
prun.resume()    Safely resume plan.
prun.abort()     Perform cleanup. Mark as aborted.
prun.stop()      Perform cleanup. Mark as success.
prun.halt()      Do not perform cleanup --- just stop.
prun.state       Check if 'paused' or 'idle'.
============== ===========

Get your data
-------------

Save images and metadata from scans
"""""""""""""""""""""""""""""""""""
These commands can be run in the ``collection-dev`` or the ``analysis`` ipython environments.
Data are saved in the directory defined in `set_experiment` FIXME (see :ref:`4. set up the file for saving output`)

**save images from last scan:**

.. code-block:: python

  save_last_tiff()

**save images from last 5 scans:**

.. code-block:: python

  h = db[-5:]
  save_tiff(h)

**save the scan 5 scans ago:**

.. code-block:: python

  h = db[-5]
  save_tiff(h)

``header`` concept `here <http://nsls-ii.github.io/databroker/headers.html>`_


Azimuthal integration
"""""""""""""""""""""

**integrate and save image(s) along with metadata from scans:**

.. code-block:: python

  integrate_and_save_last()

.. autofunction::

  xpdan.data_reduction.integrate_and_save_last

**integrate and save images from last 5 scans till now:**

.. code-block:: python

  h = db[-5:]
  integrate_and_save(h)

**save 5 scans away from now:**

.. code-block:: python

  h = db[-5]
  integrate_and_save_(h)


Global options
--------------

``glbl`` class has several attributes that control the overall behavior of ``xpdacq`` software.

Possible scenarios
""""""""""""""""""

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
