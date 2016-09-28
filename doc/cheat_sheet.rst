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

Your sample information should be loaded in an excel spreadsheet. Type

.. code-block:: python

  import_sample(300564, bt) # SAF number is 300564 to current beamtime
                            # beamtime object , bt, with SAF number 300564 has created
                            # file with 300564_sample.xls exists in ``xpdConfig`` directory

For the details of how we parse your information and create sample objects, please see :ref:`import_sample`.

Additional samples may be added by adding samples to the excel file and rerunning.

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

4. list objects by categories
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


5. interrogate metadata in objects
""""""""""""""""""""""""""""""""""

.. code-block:: python

  bt.samples[1].md        # returns metadata for item 1 in Sample list, i.e., TiO2
  bt.scanplans[5].md      # returns metadata for item 5 in scanplans list

Run your experiment
-------------------

1. A scan is a scanplan executed on a sample
""""""""""""""""""""""""""""""""""""""""""""

The main philosophy of ``xpdAcq`` is : **on this sample run this scanplan**

background scan
^^^^^^^^^^^^^^^

Running scans with ``Sample`` objects tagged as ``is_background``.

Please see :ref:`background_obj` for more information.

.. code-block:: python

  prun(48, 1) # sample 98 is ``bkg_0.5mm_OD_capillary``
  prun(49, 1) # sample 98 is ``bkg_0.9mm_OD_capillary``


.. code

production run
^^^^^^^^^^^^^^

.. code-block:: python

  prun(bt.samples[2],bt.scanplan[5]) # referencing objects explicitly
  prun(2,5)                          # inexplicit: give reference to ``Sample`` and ``ScanPlan``
                                     # index from the ``bt`` list


Get your data
-------------

1. Save images and metadata from scans
"""""""""""""""""""""""""""""""""""""

These commands can be run in the ``collection-dev`` or the ``analysis`` ipython environments.

Data are saved in the directory named after ``sample_name`` metdata you type in to ``Sample`` object.

After each command, you should see where data have been saved.

**save images from last scan:**

.. code-block:: python

  save_last_tiff()

**save images from last 5 scans:**

.. code-block:: python

  h = db[-5:]
  save_tiff(h)

**save images from scan 5 scans ago:**

.. code-block:: python

  h = db[-5]
  save_tiff(h)

We use "h" for the thing given back by databroker (``db``) to be short for "header".
This is a software object that contains all the information about your scan and can
be passed to different functions to do analysis.
more information on headers is `here <http://nsls-ii.github.io/databroker/headers.html>`_


2. Save images and also integrate images to a 1D patterns
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""

**save your images and also integrate to a 1D pattern:**

.. code-block:: python

  integrate_and_save_last()   # the most recent scan
  h = db[-5:]
  integrate_and_save(h)       # the last 5 scans
  h = db[-5]
  integrate_and_save_(h)      # the scan 5 ago


.. autosummary::
  :toctree:
  :nosignatures:

  integrate_and_save_last

Code for Sample Experiment
--------------------------

Here is a sample code covering the entire process from defining Sample`` and
``ScanPlan`` objects to running different kinds of runs.

Please replace the name and parameters in each function depending your needs.  To
understand the logic in greater detail see the full user documentation.

**Pro Tip**: copy-and-paste is your good friend

.. code-block:: python

  # bt list method to see all objects we have available for data collection
  bt.list()


  # Ideally, Sample information should be filled before you come.
  # you can fill out the spreadsheet and then use ``import_sample`` function.
  # Let's still have an example here.
  Sample(bt, 'sammple_name':'NaCl',
         {'sample_composition': {'Na':0.5, 'Cl':0.5},
          'sample_phase': {'NaCl':1},
          'composition_string': 'Na0.09Cl0.09H1.82O0.91',
          'holder':{'shape':'capillary','ID':'1 mm','madeOf':'kapton'},
          'tags':['looked kinda green','dropped on the floor during loading'],
          '<anythingElseIwant>':'<description>',
          '<andSoOn>':'<etc>'
         }  # this one will be much more useful later!


.. code-block:: python

  # define "ct" scanplan with exp = 0.5
  ScanPlan(bt, ct, 0.5)

  # define "Tramp" scanplan with exp = 0.5, startingT = 300, endingT = 310, Tstep = 2
  ScanPlan(bt, Tramp , 0.5, 300, 310, 2)
  # define "Tramp" scanplan with exp = 0.5, startingT = 310, endingT = 250, Tstep = 5
  ScanPlan(bt, Tramp, 0.5, 310, 250, 5)

  # define a "time series" scanplan with exp = 0.5, num=10, delay = 2
  ScanPlan(bt, tseries, 0.5, 2, 10)

  # Then let's do a calibration run with Ni, exposure time = 60s, and perform calibration in calibration software
  run_calibration()

  bt.list() # returns the 'NaCl' sample object at position 17 and the 'ct_0.5' ScanPlan object at position 20
  prun(17,20)

  # the data are saved into the NSLS-II database (don't worry) but we want to get the image so
  # type:
  save_last_tiff() # save tiffs from last scan

  # now we have everything set up, it is super-easy to sequence lots of interesting scans
  # this does a series of different scans on the same sample
  prun(17,21)   # assume 'Tramp_0.5_300_310_2' ScanPlan object at position 21
  prun(17,22)   # assume 'Tramp_0.5_310_250_5' ScanPlan object at position 23
  save_tiff(db[-3:]) # save tiffs from last three scans

  # this does the same scan on a series of samples
  prun(17,21)   # running sample at index 17 with 'Tramp_0.5_300_310_2' ScanPlan
  prun(18,21)   # running sample at index 18 with 'Tramp_0.5_300_310_2' ScanPlan
  prun(19,21)   # running sample at index 19 with 'Tramp_0.5_300_310_2' ScanPlan
  save_tiff(db[-3:]) # save tiffs from last three scans


Interrupt your scan
--------------------

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
