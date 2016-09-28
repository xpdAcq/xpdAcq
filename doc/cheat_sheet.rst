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

  import_sample(300064, bt) # SAF number is 300064 for example

your spreadsheet should located inside ``xpdConfig`` directory with name as ``<saf_number>_sample.xls``.

``Sample`` objects corresponding each row of your spreadsheet will be
created, along with corresponding background object. for the parsing rule, please see :ref:`import_sample`

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


Get your data
-------------

1. Save images and metadata from scans
"""""""""""""""""""""""""""""""""""""

These commands can be run in the ``collection-dev`` or the ``analysis`` ipython environments.
Data are saved in the directory defined in `set_experiment` FIXME (see :ref:`4. set up the file for saving output`)

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

Here is a sample code covering the entire process from defining ``Experiment``,
``Sample`` and ``ScanPlan`` objects to running ``ScanPlans`` with different kinds of run.
Please replace the name and parameters in each function depending your needs.  To
understand the logic in greater detail see the full user documentation.

**Pro Tip**: copy-and-paste is your good friend

.. code-block:: python

  # bt list method to see all objects we have available for data collection
  bt.list()
  
  # bt list of all the Sample objects but no other object types
  bt.list('sa')
  
  # bt list of all the ScanPlan objects but no other object types
  bt.list('sp')

  # define addtional acquire objects
  Experiment('myExperiment', 
             bt, 
             {'<mynewkeys>':'<mynewvalues>',
              'examples':'follow',
              'students':['sbanerjee','mterban'],
              'collaborators':['Sample Maker','Sam Student']
             }
            )  
  bt.list()    # returns 'myExperiment' object at position (index) 11 in the list 
  Sample('myLazySample', bt.get(11))    # it will inherit all metadata in the bt and 'myExperiment' objects but we were lazy, we didn't save any sample info!

  # here is a more useful sample description.  Ideally, make these at home before you come, 
  # then export them as yaml files ('export_user_metadata' [FIXME]), bring them to the beamtime on a flash drive
  # then import them when your experiment is set up ('import')
  Sample('NaCl_0.1', 
         bt.get(11),
         {'phases':[{'composition':'NaCl',
                     'mass_fraction':0.1,
                     'cif':'NACL.cif',
                     'ICSD-ID':'2439d-13'
                     'form':'powder'
                    },
                    {'composition':'CaCO4.H2O',
                     'mass_fraction':0.9,
                     'cif':'hydratedCalciumCarbonate.cif',
                     'form':'nanopowder'
                    }
                   ],
          'holder':{'shape':'capillary','ID':'1 mm','madeOf':'kapton'},
          'notes':['looked kinda green','dropped on the floor during loading'],
          '<anythingElseIwant>':'<description>',
          '<andSoOn>':'<etc>'
         }  # this one will be much more useful later!


.. code-block:: python

  # define "ct" scanplan with exp = 0.5
  ScanPlan('ct_0.5','ct',{'exposure':0.5})

  # define "Tramp" scanplan with exp = 0.5, startingT = 300, endingT = 310, Tstep = 2
  # define "Tramp" scanplan with exp = 0.5, startingT = 310, endingT = 300, Tstep = 2
  ScanPlan('Tramp_0.5_300_310_2','Tramp',{'exposure':0.5, 'startingT': 300, 'endingT': 310, 'Tstep':2})
  ScanPlan('Tramp_0.5_310_300_2','Tramp',{'exposure':0.5, 'startingT': 310, 'endingT': 300, 'Tstep':2})
  
  # or use the short-form
  ScanPlan('Tramp_0.5_300_310_2') # which builds the scan parameters from the name itself (but don't get them in the wrong order!)

  # define a "time series" scanplan with exp = 0.5, num=10, delay = 2
  ScanPlan('tseries_0.5_2_5', 'tseries', {'exposure':0.5, 'num':5, 'delay':2})
  # or
  ScanPlan('tseries_0.5_2_5')

  # do a dry-run to see what the program will do, and what metadata it will save
  dryrun('NaCl_0.1', 'ct_0.5')

  # Then let's do a calibration run and save the image in order to open it in calibration software
  calibration([FIXME])
  save_last_tiff()

  # Use setupscan to check image quality under current scan parameters
  setupscan([FIXME])
  save_last_tiff()

  # Everything looks right. Let's do prun with different ScanPlans and save the tiffs
  prun('NaCl_0.1','ct_0.5')
  # or
  bt.list() # returns the 'NaCl_0.1' sample object at position 17 and the 'ct_0.5' ScanPlan object at position 20
  prun(17,20)
  
  # the data are saved into the NSLS-II database (don't worry) but we want to get the image so
  # type:
  save_last_tiff() # save tiffs from last scan
  
  # now we have everything set up, it is super-easy to sequence lots of interesting scans
  # this does a series of different scans on the same sample
  prun(17,21)   # or prun(17,'Tramp_0.5_300_310_5'), whichever you are more comfortable with.
  prun(17,22)   # or prun('NaCl_0.1','Tramp_0.5_310_300_5'), or whatever
  prun(17,23)
  save_tiff(db[-3:]) # save tiffs from last three scans

  # this does the same scan on a series of samples
  prun(17,21)   # or prun('NaCl_0.1,'Tramp_0.5_300_310_5'), whichever you are more comfortable with.
  prun(18,21)   # or prun('NaCl_0.2','Tramp_0.5_300_310_5'), or whatever,
  prun(19,21)   # or prun('NaCl_0.3',21),
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


