.. _cheat_sheet:

Cheat Sheet
===========

This cheat-sheet contains no explanation of how the ``xpdAcq`` software works.
To understand this, please refer to the detailed documentation in :ref:`xpdu`

Please use this page as a reminder of the workflow and to copy & paste code snippets into your
active ``collection`` and ``analysis-dev`` ipython environments (then hit return).

Remember, to post questions about anything XPD, including software, and to see archived answers, please visit the `XPD-Users Google group 
<https://groups.google.com/forum/#!forum/xpd-users;context-place=overview>`_

Check your data collection environment is correctly set up
----------------------------------------------------------

1. Make sure you are working in the correct environment. For data acquisition you should be
in the ``collection`` ipython environment (look for ``(collection)`` at the beginning
of the command prompt).  If you can't find a terminal with ``collection`` running, then
start it by opening a new terminal and typing 

.. code-block:: python

  icollection

2. Make sure that the software has been properly configured for your beamtime. In
your ``collection`` environment, type:

.. code-block:: python

  bt.md

This should return a list of metadata about your experiment, such as PI last name.  If not
please get your beamtime environment set up by the instrument scientist before proceeding.

Check that your data analysis environment is correctly set up
-------------------------------------------------------------

1. Analysis is done in a separate (but very similar) environment to acquisition. 
For data analysis you should be
in the ``analysis-dev`` ipython environment (look for ``(analysis-dev)`` at the beginning
of the command prompt).  Ideally, this should be running on a different computer than the
acquisition, but looking at a shared hard-drive so that it can find files.

If you can't find a terminal with ``(analysis-dev)`` running, then
start it by opening a new terminal and typing 

.. code-block:: python

  ianalysis

2. Make sure that the software has been properly configured for your beamtime. In
your ``analysis`` environment, type:

.. code-block:: python

  an.md

This should return a list of metadata about your experiment, such as PI last name.  If not
please get your analysis environment set up by the instrument scientist before proceeding.

3. Make sure the visualization software is running. We will use XPDsuite for visualizing data.  
Check that it is running by finding a window that looks like:

FIXME

If you can't find it, contact your IS to get it running correctly.

Set up your experiment
----------------------
0. general
""""""""""

If you want to query any xpdAcq function, type the function name with a `?` at the end and hit
return.  Documentation for what paramters the function takes, and any default values, and what
the function returns will be printed.  For example, type:

.. code-block:: python

  run_calibration?

If you can't remember what functions are available, but can remember the first letter or first few
letters, type those letters and hit `tab` to see a list of all available functions that begin with 
those letters.

1. calibration
""""""""""""""
run this first, then run it again each time the geometry of your measurement changes.  

Place the Ni calibrant at the sample position.  Let's make sure we are getting a nice
Ni diffraction pattern. Type:

.. code-block:: python

  prun(0,0) # will run an exposure of 60 seconds on your Ni sample
  save_last_tiff()
  
Navigate to XPDsuite, click on the 2D image plotter (green button that looks like FIXME).
In the image plotter, called SrXplanar, select open_files FIXME naviage to the ``Ni_calibrant``
directory and look for the latest tiff image. FIXME

.. code-block:: python

  run_calibration() # default values: calibrant_file='Ni.D' and exposure=60

and follow the instructions in :ref:`calib_manual`

2. set up mask
""""""""""""""

The automasking has been extensively tested on a low-scattering sample so our mask 
building function has been designed to run on data from an empty kapton tube.  
Load an empty kapton tube on the diffractometer, then type

.. code-block:: python

  run_mask_builder() # be patient, the process takes 10 minutes!

A mask will be generated based on the image collected from this sample. This mask
will be saved for use with all future datasets until you run ``run_mask_builder()``
again.

For more info: :ref:`auto_mask`.


3. set up ``Sample`` objects to use later
"""""""""""""""""""""""""""""""""""""""""

Your sample information should be loaded in an excel spreadsheet, with a well
defined format (a template file may be found `here 
<https://groups.google.com/forum/?utm_medium=email&utm_source=footer#!topic/xpd-users/_6NSRWg_-l0>`_ 
). If the IS didn't already
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

where the ``saf_number`` is ``300564``.

To load the sample information and have the sample objects available in the current beamtime:

.. code-block:: python

  import_sample()

updates and additions may be made by adding more samples to the excel file and rerunning ``import_sample()``
at any time during the experiment.

For more info :ref:`import_sample`.


4. set up ``ScanPlan`` objects to use later
"""""""""""""""""""""""""""""""""""""""""""

use an xpdAcq template
^^^^^^^^^^^^^^^^^^^^^^

``xpdAcq`` has templates for three common scans (more will follow, please request yours at `xpd-users Google group! 
<https://groups.google.com/forum/#!forum/xpd-users;context-place=overview>`_ ): a
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
a specific list of points while collecting an image at each point from ``area_detector``, which uses a bluesky
predefined plan, ``list_scan``, can be run as below:

.. code-block:: python

  from bluesky.plans import list_scan
  
  glbl.area_det.images_per_set.put(600)  # 60s exposure if continuous acquisition with 0.1s framerate
  myplan = list_scan([area_detector], motor, [1,3,5,7,9]) # drives motor to postion 1,3,5,7,9
  myplan = subs_wrapper(myplan, LiveTable([area_detector])) # LiveTable will give updates on how the scan is progressing
  prun(56, myplan) # run this scanplan on sample 56

You may also write your own bluesky plans and run them similar to the above.
For more details about how to write a ``bluesky`` scan plan,
please see `here <http://nsls-ii.github.io/bluesky/plans.html>`_.

It is recommended to use xpdAcq template ScanPlans where you can so that metadata is saved in a
standardized way for easier later searching.

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
setup, for example, crystalline peaks due to the beam hitting a shutter, for example.

 1. Load the background sample (e.g., empty kapton tube) on the instrument
 2. list your sample objects and find the ones tagged as backgrounds in the excel spreadsheet
 3. run prun (see below) on the background sample with a ``ct`` ScanPlan object of the desired exposure

Please see :ref:`background_obj` for more information.

How long should you run your background scan for? See discussion 
`here <https://groups.google.com/forum/#!topic/xpd-users/RvGa4pmDbqY>`_

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

With this function, the image will be saved to a ``.tiff`` file.
The metadata associated with the image will be saved to a ``.yml`` file which is a
text file and can be opened with a text editor.  Saving behavior
can be modified by changing the default function arguments.  Type ``save_last_tiff?``
to see the allowed values.

**Pro Tip**: this function is often typed just after ``prun()`` in the collection environment,
so that the data are extracted out of the NSLS-II database and delivered to you automatically when
the scan finishes.  You can then play around with them and take them home as you like.  

The following
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

We use "h", short for "header", for the object given back by the NSLS-II databroker (``db``) data-fetching software.
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


.. code-block:: python

  # the most recent scan with mask applied
  integrate_and_save_last()

With this function, the image will be saved to a ``.tiff`` file, the mask will be saved
to a ``.npy`` file, and the masked-image will be integrated and saved to a ``.chi`` file.
The metadata associated with the image will be saved to a ``.yml`` file which is a
text file and can be opened with a text editor.  Masking and calibration behavior
can be modified by changing the default function arguments.  Type ``integrate_and_save_last?``
to see the allowed values.

User scripts
------------

  Your ``scanplan`` objects can be sequenced into scripts, executing one after the other as you desire.  To set this up, write a sequence of commands into a text file, save it with the extension ``.py`` in the ``userScripts`` directory with a memorable name, like ``myNightShiftScript.py``.  Double and triple check your script, then when you are ready to execute it, in ``ipython`` session type:


  .. code-block:: python

    %run -i ~/xpdUser/userScripts/myNightShiftScript.py

  Stay there for a while to make sure everything is running as expected and then go to bed!

Code for Example Experiment
--------------------------

Here is a sample code covering the entire process from defining ``Sample`` and
``ScanPlan`` objects to running different kinds of runs.

Please replace the name and parameters in each function depending your needs.  To
understand the logic in greater detail see the full user documentation.

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
