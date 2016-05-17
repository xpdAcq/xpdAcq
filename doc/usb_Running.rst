.. _usb_running:

Running scans
-------------

The hard work of the experimental setup is now done.  It involved creating all the
rich metadata container and ScanPlan objects, but with this in the past it makes
it easy and low overhead to run the scans, allowing the experimenter to concentrate
on the science and not the experimental process.

To run scans there are just a few xpdAcq
run engines(functions) that you need.  To run a scan you simply pick the run engine you want
and give it a predefined Sample object and
a predefined ScanPlan object, then hit return and sit back, your scan will be carried out.

The allowed scan types are:

.. code-block:: python

  >>> prun(sample, scanplan)
  >>> dark(sample, scanplan)
  >>> background(sample, scanplan)
  >>> calibration(sample, scanplan)
  >>> setupscan(sample, scanplan)
  >>> dryrun(sample, scanplan)

.. autofunction:: xpdacq.xpdacq.prun

``prun`` stands for "production run" which is a normal run.

.. autofunction:: xpdacq.xpdacq.dark

``dark`` collects dark frames.Strictly speaking the sample is irrelevant here because the shutter is closed, but
it is left in the definition for consistency and in general ``dark`` is not necessary as automated dark subtraction collect dark images for you.

.. autofunction:: xpdacq.xpdacq.calibration

``calibration`` is specifically designed to collect image on your calibrants.

.. autofunction:: xpdacq.xpdacq.setupscan

``setupscan`` is for testing things before you are ready to get production data, such as trying out different exposures
on a sample to find the best exposure time.

.. autofunction:: xpdacq.xpdacq.dryrun

``dryrun`` does not execute any scan but tells you what is going to be run when you give the same Sample and Scan objects
to any of the other runs. It may be used for validating your scan objects, and also for estimating how long a ``tseries`` or ``Tramp`` might take.

Here are some examples of a workflow.  Assume a GaAs sample is loaded on the diffractometer
and the ``'GaAs'`` Sample object is created as well as all the ScanPlans we need.
We will start by doing a dry-run on our ``'ct2'`` count ScanPlan.

Remember, always start with ``bt.list()``

.. code-block:: python

  >>> bt.list()
  bt object bt has list index  0
  ex object InGaAsAlloyPD has list index  1
  ex object ProteinFolding has list index  2
  sa object GaAs has list index  3
  sa object IGA75-25 has list index  4
  sa object In0.25Ga0.75As has list index  5
  sa object InAs has list index  6
  sa object InGaAs-5050 has list index  7
  sc object ct1.5 has list index  8
  sc object ct1.5_nosh has list index  9
  sc object ct100.5_nolt has list index  10
  sc object ct2 has list index  11
  sc object ct2_vw has list index  12
  sc object ct2_vw_nos has list index  13
  sc object ct2_vw_nosh has list index  14
  Use bt.get(index) to get the one you want

The Sample object I want has list index 3 and the ScanPlan has list index 11.
Let's try a dryrun to make sure everything is ok.

.. code-block:: python

  >>> dryrun(bt.get(3),bt.get(11))
  INFO: requested exposure time =  2.0  -> computed exposure time: 2.0
  === dryrun mode ===
  this will execute a single bluesky Count type scan
  Sample metadata: Sample name = GaAs
  using the "pe1c" detector (Perkin-Elmer in continuous acquisition mode)
  in the form of 20 frames of 0.1 s summed into a single event
  (i.e. accessible as a single tiff file)

OK, it seems to work, lets do some testing to see how much intensity we need.
We will do three setup scans with 1.5 seconds and 100.5 seconds exposure
and then compare them.

.. code-block:: python

  >>> setupscan(bt.get(3),bt.get(8))   #1.5 seconds
  >>> setupscan(bt.get(3),bt.get(10))  #100.5 seconds
  INFO: requested exposure time =  1.5  -> computed exposure time: 1.5
  +-----------+------------+------------------+
  |   seq_num |       time | pe1_stats1_total |
  +-----------+------------+------------------+
  |         1 | 10:49:31.3 |                0 |
  +-----------+------------+------------------+
  Count ['e7adbd'] (scan num: 1)
  INFO: requested exposure time =  100.5  -> computed exposure time: 100.5
  +-----------+------------+------------------+
  |   seq_num |       time | pe1_stats1_total |
  +-----------+------------+------------------+
  |         1 | 10:49:41.3 |                0 |
  +-----------+------------+------------------+
  Count ['e7adbd'] (scan num: 2)

what is nice about these is that they are tagged with an ``sc_isprun':False`` metadata field
which means that, by default, they will not be retrieved when searching for production data.  It
keeps our setup scans and production scans nicely separated in the database, though
the underlying scans that are carried out are all still there and can be retrieved if need
be.

It seems that the 2 second scans are the best, so let's do a production run
to get the first data-set.

.. code-block:: python

  >>> prun(bt.get(3),bt.get(11))  #2 seconds
  INFO: auto_dark didn't detect a valid dark, so is collecting a new dark frame.
  See documentation at http://xpdacq.github.io for more information about controlling this behavior
  INFO: requested exposure time =  2.0  -> computed exposure time: 2.0
  +-----------+------------+------------------+
  |   seq_num |       time | pe1_stats1_total |
  +-----------+------------+------------------+
  |         1 | 10:51:36.6 |                0 |
  +-----------+------------+------------------+
  Count ['d475dc'] (scan num: 1)
  INFO: requested exposure time =  2.0  -> computed exposure time: 2.0
  +-----------+------------+------------------+
  |   seq_num |       time | pe1_stats1_total |
  +-----------+------------+------------------+
  |         1 | 10:51:42.4 |                0 |
  +-----------+------------+------------------+
  Count ['e7adbd'] (scan num: 2)

.. _auto_dark_collect:

Automated dark frame collection
""""""""""""""""""""""""""""""""

So far, you might have found something weird from the output shown above.
We only requested *one* ``prun`` but program runs *two* scans. So what happen?

That is actually a wonderful feature called auto-dark subtraction of ``xpdAcq``.
When you are running your experiment, ``xpdAcq`` actually checks if you have
collected a **fresh** dark frame every time it collects a scan.
The definition of **fresh** is:

.. code-block:: none

  Given a certain period T (called dark window), there is a dark frame
  with the same exposure time as the light frame we are about collect.

Automated dark collection is enabled by default and it can be turned off
by either of these ways:

.. code-block:: python

  >>> glbl.auto_dark = False # turn it off for all scans measured afterwards
  >>> prun(bt.get(3),bt.get(11), auto_dark = False) # only turn it off for this scan

And period of dark window can be modified by:

.. code-block:: python

  >>> glbl.dk_window = 200 # in minutes. default is 3000 minutes

Having ``auto_dark`` set to ``True`` is strongly recommended as this enables
``xpdAcq`` to do automated dark frame subtraction when you pull out data from
centralized **NSLSL-II** server.


.. _auto_calib:

Automated calibration loading
"""""""""""""""""""""""""""""

Often times, keeping track with which calibration file is associated with
certain scan is very tiring. ``xpdAcq`` makes this easier for you. Before every
scan is being collected, program goes to grab the most recent calibration
parameters in ``/home/xf28id1/xpdUser/config_base`` and load them as part of
metadata so that you can reference them whenever you want and make in-situ data
reduction possible!

Let's :ref:`take a quick look at our data <usb_quickassess>`
