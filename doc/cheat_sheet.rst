.. _cheat_sheet:

Code for Example Experiment
--------------------------

Here is a sample code covering the entire process from defining ``Sample`` and
``ScanPlan`` objects to running different kinds of runs.

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
