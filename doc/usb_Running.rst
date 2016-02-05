.. _usb_running:

Running scans
-------------

The hard work of the experimental setup is now creating all the objects, making
it easy and low overhead to run the scans.  There are just a few xpdAcq
run engines that you need.  Each on you simply give a Sample object and
a ScanPlan object and hit return, and your scan will be carried out.

The allowed scan types are:

.. code-block:: python

  >>> prun(sample,scan)
  >>> dark(sample,scan)
  >>> setupscan(sample,scan)
  >>> dryrun(sample,scan)
  
``prun`` stands for "production run" which is a normal run.  ``dark`` collects dark frames.
Strictly speaking the sample is irrelevant here because the shutter is closed, but
it is left in the definition for consistency.  ``setupscan`` is for testing things
before you are ready to get production data, such as trying out different exposures
on a sample to find the best exposure time.  ``dryrun`` does not execute any scan
but tells you what is going to be run when you give the same Sample and Scan objects
to any of the other runs.  It may be used for validating your scan objects, and
also for estimating how long a ``tseries`` or ``Tramp`` might take.

Here are some examples of a workflow.  Assume a GaAs sample is loaded on the diffractometer
and the ``'GaAs'`` Sample object is created as well as all the ScanPlans we need.
We will start by doing a dry-run on our ``'ct2"`` count ScanPlan.

. code-block:: python

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
  [Fixme] output here

OK, it seems to work, lets do some testing to see how much intensity we need.
We will do three setup scans with 1.5 second, 2 seconds and 100.5 seconds exposure 
and then compare them.

.. code-block:: python

  >>> setupscan(bt.get(3),bt.get(8))   #1.5 seconds
  >>> setupscan(bt.get(3),bt.get(11))  #2 seconds
  >>> setupscan(bt.get(3),bt.get(10))  #100.5 seconds
  [Fixme] output here

what is nice about these is that they are tagged with an ``'xp_isprun':True`` metadata field
which means that, by default, they will not be retrieved when searching for production data.  It
keeps our setup scans and production scans nicely separated in the database, though
the underlying scans that are carried out are the same.
