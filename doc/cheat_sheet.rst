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

2. set up mask
""""""""""""""
put in a sample that you want your mask to be generated from. You may use any
sample that is relevant to your experiment, but we recommend using a weak scattering
sample such as an empty kapton tube.

Then type

.. code-block:: python

  run_mask_builder()

A mask will be generated based on image collected from this sample. This mask
will be saved for use with all future datasets until you run ``run_mask_builder()``
again.

For more info: :ref:`auto_mask`.


3. set up ``Sample`` objects to use later
"""""""""""""""""""""""""""""""""""""""""

Your sample information should be loaded in an excel spreadsheet, with a well
defined format (a template file may be found here FIXME). If the IS didn't already
do it, save your sample xls file to the ``xpdConfig`` directory using the name
``<saf_number>_sample.xls``, where you replace ``<saf_number>`` with the number
of the safety approval form associated with you experiment.  If you are not sure
what your ``saf_number`` is you can get it by typing:

.. code-block:: python

  In[1] bt
  Out[1]:
  {'bt_experimenters': ['Tim', 'Liu'],
   'bt_piLast': 'Billinge',
   'bt_safN': '300564',
   'bt_uid': 'f4eda7ec',
   'bt_wavelength': 0.1832}

Here you can see your saf_number under ``bt_safN`` field. In this code example,
``saf_number`` is ``300564``.

To load the sample information and have the sample objects available in the current beamtime:

.. code-block:: python

  import_sample()

updates and additions may be added by adding more samples to the excel file and rerunning ``import_sample()``
at any time during the experiment.

For more info :ref:`import_sample`.


4. set up ``ScanPlan`` objects to use later
"""""""""""""""""""""""""""""""""""""""""""

use an xpdAcq template
^^^^^^^^^^^^^^^^^^^^^^

``xpdAcq`` has templates for three common scans (more will follow, please request yours at ``xpd-users`` Google group!): a
simple count, a series of counts, and a temperature scan.  Use the template to create specific Plans (that include specific start and
stop temperatures, count times and so on) using the following table as a template.  These can be created now (to save time later) or
later when you need them.

======================================= ===================================================================================
command
======================================= ===================================================================================
``ScanPlan(bt, ct, 5)``                  a count scan for 5s

``ScanPlan(bt, tseries, 5, 50, 15)``     time series with 5s count time, 50s delay and 15 repeats

``ScanPlan(bt, Tramp, 5, 300, 200, 5)``  temperature series with 5s count time, starting from 300k to 200k with 5k per step
======================================= ===================================================================================

write your own scan plan
^^^^^^^^^^^^^^^^^^^^^^^^

``xpdAcq`` also consumes any scan plan from ``bluesky``. For example, a scan that drives a ``motor`` through
a specific list of points while collecting read-back value from ``area detector`` can be defined and run as below:

.. code-block:: python

  from bluesky.plans import list_scan
  myplan = list_scan([area_detector], motor, [1,3,5,7,9]) # drives motor to postion 1,3,5,7,9
  prun(56, myplan) # run this scanplan on sample 56


For more details about how to write a ``bluesky`` scan plan,
please see `here <http://nsls-ii.github.io/bluesky/plans.html>`_.

It is recommended that you use the ``xpdAcq`` templates unless your experiment needs its own special
bluesky plan, because the autoreduction of data is not currently supported for bluesky pass-through plans.
Also, metadata capture in bluesky passthrough plans must be explicitly coded into the plan.

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

The main philosophy of ``xpdAcq`` is : **on this sample run this scanplan**

background scan
^^^^^^^^^^^^^^^

It is recommended to run a background scan before your sample so it is available for
the automated data reduction steps.  It also allows you to see problems with the experimental
setup, for example, crystlline peaks due to the beam hitting a shutter, for example.

 1. Load the background sample (e.g., empty kapton tube) on the instrument
 2. list your sample objects and find the ones tagged as backgrounds in the excel spreadsheet
 3. run prun (see below) on the background sample with a ``ct`` ScanPlan object of the desired exposure

Please see :ref:`background_obj` for more information.

production run
^^^^^^^^^^^^^^

 1. Load your sample
 2. List your sample objects to find the right one
 3. type prun with the desired sample object and ScanPlan (see below)

.. code-block:: python

  prun(bt.samples[2],bt.scanplan[5]) # referencing objects explicitly
  prun(2,5)                          # inexplicit: give reference to ``Sample`` and ``ScanPlan``
                                     # index from the ``bt`` list

For more info: FIXME

Get your data
-------------

1. Save images and metadata from scans
""""""""""""""""""""""""""""""""""""""

These commands can be run in the ``collection`` or the ``analysis`` ipython environments.

Data are saved in the directory ``xpdUser/tiff_base/<sample_name>`` where ``<sample_name>`` is the name of the
sample that you used in the sample spreadsheet, and is the name of the ``Sample`` object.

**save images from last scan:**

.. code-block:: python

  save_last_tiff()

**Pro Tip**: this function is often typed just after ``prun()`` in the collection environment,
so that the data are extracted out of the NSLS-II database and delivered to you automatically when
the scan finishes.  You can then play around with them and take them home as you like.  The following
functions are more useful for running in the ``analysis`` environment to fetch scans from the database
selectively if you don't want a dump of every scan.

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
  h = db[-5:]                 # the last 5 scans
  integrate_and_save(h)
  h = db[-5]                  # the scan 5 ago
  integrate_and_save_(h)



during this integration/saving process, you can choose if you want to apply
``mask`` to your image by option ``auto_mask``

.. code-block:: python

  # the most recent scan with mask applied
  integrate_and_save_last()
  # the most recent scan, no mask applied
  integrate_and_save_last(auto_mask=False)

.. note::

  image saved will **NOT** be masked, mask is only handed in during integration
  step. masked used will be saved separately.


Code for Sample Experiment
--------------------------

Here is a sample code covering the entire process from defining ``Sample`` and
``ScanPlan`` objects to running different kinds of runs.

Please replace the name and parameters in each function depending your needs.  To
understand the logic in greater detail see the full user documentation.

**Pro Tip**: copy-and-paste is your good friend

.. code-block:: python

  # bt list method to see all objects we have available for data collection
  bt.list()


  # Ideally, Sample information should be filled before you come.
  # you can fill out the spreadsheet and then use ``import_sample`` function.
  # Let's still have an example here of how to do it explicitly
  Sample(bt, 'sammple_name':'NaCl',
         {'sample_composition': {'Na':0.5, 'Cl':0.5},
          'sample_phase': {'NaCl':1},
          'composition_string': 'Na0.09Cl0.09H1.82O0.91',
          'holder':{'shape':'capillary','ID':'1 mm','madeOf':'kapton'},
          'tags':['looked kinda green','dropped on the floor during loading'],
          '<anythingElseIwant>':'<description>',
          '<andSoOn>':'<etc>'
         }  # rich metadata will save a lot of time later!


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

FIXME: if we have a ``view_last_image()`` function, document this one too.

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
