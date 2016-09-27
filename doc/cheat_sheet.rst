.. _cheat_sheet:

Cheat Sheet
===========

Please use this page as a reminder and copy&paste code snippets into your  ``ipython`` terminals.

To understand what the code does, please go :ref:`qs` or :ref:`xpdu`

Running experiment
-------------------

.. note::

  commands realted to *collection* must be executed under ``collection-dev`` profile

calibration
"""""""""""

.. code-block:: python

  run_calibration(exposure=60) # assume calibrant is Ni

short tutorial about calibration here :ref:`calib_manual`

.. autofunction::

  xpdacq.calib.run_calibration

set up ``Sample`` objects
""""""""""""""""""""""""

Example:

.. code-block:: python

  Sample(bt, {'sample_name':'Ni', 'sample_composition':{'Ni':1}} )
  Sample(bt, {'sample_name':'TiO2', 'sample_composition':{'Ti':1, 'O':2}})
  import_sample(saf_num=300064, bt)

set up ``ScanPlan`` objects
"""""""""""""""""""""""""""

Example:

======================================= ===================================================================================
command
======================================= ===================================================================================
``ScanPlan(bt, ct, 5)``                  a count scan for 5s

``ScanPlan(bt, tseries, 5, 50, 15)``     time series with 5s count time, 50s delay and 15 repeats

``ScanPlan(bt, Tramp, 5, 300, 200, 5)``  temperature series with 5s count time, starting from 300k to 200k with 5k per step
======================================= ===================================================================================

list objects by categories
"""""""""""""""""""""""""""

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


interrupt
"""""""""

table from `original package <http://nsls-ii.github.io/bluesky/state-machine.html#interactive-pause-summary>`_


Interactively Interrupt Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

======================= ===========
Command                 Outcome
======================= ===========
Ctrl+C                  Pause soon.
Ctrl+C twice            Pause now.
Ctrl+C three times fast (Shortcut) Pause now and abort.
======================= ===========

From a paused state
^^^^^^^^^^^^^^^^^^^

============== ===========
Command        Outcome
============== ===========
prun.resume()    Safely resume plan.
prun.abort()     Perform cleanup. Mark as aborted.
prun.stop()      Perform cleanup. Mark as success.
prun.halt()      Do not perform cleanup --- just stop.
prun.state       Check if 'paused' or 'idle'.
============== ===========

Access to your data
-------------------

.. note::

  commands realted to *analysis* must be executed under ``analysis`` profile

Save images and metadata from scans
"""""""""""""""""""""""""""""""""""""

``header`` concept `here <http://nsls-ii.github.io/databroker/headers.html>`_

**save images from last scan:**

.. code-block:: python

  save_last_tiff()

**save images from last 5 scans till now:**

.. code-block:: python

  h = db[-5:]
  save_tiff(h)

**save 5 scans away from now:**

.. code-block:: python

  h = db[-5]
  save_tiff(h)

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
