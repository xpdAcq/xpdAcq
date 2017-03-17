.. _usb_scan:

ScanPlan objects
----------------

Firstly, what is a scanplan?  A scanplan is a grouped set of detector exposures.  The set may
contain just one exposure (we call that a count scan, ``'ct'`` ).  Or it may be a series of exposures
taken one after the other, possibly with a delay between.  We
call that a time-series (or ``'tseries'`` ).  We also support two kinds of temperature related scanplans, which are temperature ramp, ``'Tramp'`` and temperature list, ``Tlist``. More are also on the way, but
these simple scanplans may also be combined together in scripts, giving the user significant
control over how to construct their experiment.
Firstly, what is a ScanPlan?  A ``ScanPlan`` is a grouped set of detector exposures.  The set may
contain just one exposure (we call that a count scan, ``ct`` ).  Or it may be a series of exposures
taken one after the other, possibly with a delay between.  We call that a time-series (or ``tseries`` ).
Other temperature-related plans supported are temperature ramp, ``Tramp`` and temperature list scan, ``Tlist``.
More are also on the way, but these simple ``ScanPlan`` may also be combined together in scripts,
giving the user significant control over how to construct their experiment.

To run a scan we need a ``ScanPlan`` and a ``Sample``.  The ``ScanPlan`` is the detailed description of
what the scan will do, but it doesn't generate *any* scan until it is run on a particular sample.
Separating a scan into a plan and an execution (which is different than how SPEC works
for those old enough) makes it very easy to run a number of different samples with the
exact same ``ScanPlan``, or (if you really want to) to collect dark images with exactly the same scan pattern, and so on.
We also want to save scan metadata accurately when the scan is actually run.  To ensure this,
each scan object takes the scanplan parameters and it uses the same parameters
both to run the scan at run-time, and to save them, along with the sample information,
in the metadata for each exposure.

With this in mind, the workflow is that *we never edit a ScanPlan and rerun it* (stop that you SPEC people!).
What we do is that we **create a new ScanPlan object**,
every time we want to do a different, *even slightly different*, scan. These are all
saved for reload and will be sent home with you at the end of the experiment.

Setting up ScanPlans
""""""""""""""""""""

``ScanPlan`` takes ``Beamtime``, scanplan and corresponding arguments. Let's type ``ScanPlan?`` and hit return to find out more:

.. autofunction:: xpdacq.beamtime.ScanPlan


Here are some examples of valid count-type ScanPlan definitions:

.. code-block:: python

  >>> sc = ScanPlan(bt, ct, 5)                      # the simplest count scan definition

A few things to note:
  * First argument is always ``bt``, the ``Beamtime`` object.
  * The second argument is always the scanplan. In the example above, we
    are using *count*, so we use ``ct`` as the second argument.
  * The scan parameter is fed in after scan type, starting from the third positional argument.

Types of ScanPlan available in current version:
  * ``ct`` just exposes the detector for a number of seconds. e.g.,  ``ScanPlan(bt, ct, 17.5)``
  * ``tseries`` executes a series of ``num`` counts of exposure time ``exposure`` seconds with  a delay of ``delay`` seconds between them.  e.g., ``ScanPlan(bt, tseries, 1, 59, 50)`` will measure 50 scans of 1 second with a delay of 59 seconds in between each of them.
  * ``Tramp`` executes a temperature ramp from ``'startingT'`` to ``'endingT'`` in temperature steps of ``Tstep`` with exposure time of ``exposure``.  e.g., ``ScanPlan(bt, Tramp, 1, 200, 500, 5)`` will automatically change the temperature,
    starting at 200 K and ending at 500 K, measuring a scan of 1 s at every 5 K step. The temperature controller will hold at each temperature until the temperature stabilizes before starting the measurement.
  * ``Tlist`` exposes the detector for a given exposure time ``exposure``
    in seconds at each temperature from a user-defined temperature
    list. For example, ``ScanPlan(bt, Tlist, 20, [250, 180, 200, 230])``
    will drive the temperature controller to 250K, 180K, 200K and 230K
    and expose the detector for 20 seconds after the temperature
    controller equilibrates at each of the temperatures.

Summary table on ScanPlan
"""""""""""""""""""""""""""

  =========== ================================================ ==================================================================================
  ScanPlan    Syntax                                            Summary
  =========== ================================================ ==================================================================================
  ``ct``      ``ScanPlan(bt, ct, 17.5)``                       a count scan for 17.5s
  ``tseries`` ``ScanPlan(bt, tseries, 1, 59, 50)``             time series with 1s count time, 59s delay and 50 repeats
  ``Tramp``   ``ScanPlan(bt, Tramp , 1, 200, 500, 5)``         temperature series with 1s count time, starting from 300k to 200k with 5k per step
  ``Tlist``   ``ScanPlan(bt, Tlist, 5, [250, 180, 200, 230])`` exposure detector for 5s at 250K, 180K, 200K and 230K
  =========== ================================================ ==================================================================================

.. _customize_scan:

Write your own ScanPlan
""""""""""""""""""""""""

``xpdAcq`` also consumes any scan plan from ``bluesky``. The ability to write your own bluesky plans gives enormous flexibility
but has a steep learning curve, but you should be able to get help setting these up from your local contact. For more details about how to write a ``bluesky`` scan plan,
please see `full document <http://nsls-ii.github.io/bluesky/plans.html>`_.

Here we will show a brief example for illustration. The specific illustration is a scan that drives a motor called ``motor`` through a specific list of points while collecting
an image at each point from the detector ``area_detector``.  It uses a predefined ``bluesky``
plan for this purpose, ``list_scan``.  To use this in ``xpdAcq`` you would first define your ``bluesky`` plan
and assign it to the object we have called ``mybsplan`` in this example:

.. code-block:: python

  from bluesky.plans import list_scan

  # it is entirely optional to add metadata to the scan, but here is what you would do:
  mymd = {'memoy_aid': 'This metadata should be about the scan, not the sample which would be added when the scanplan is run',
          'author': 'Simon',
          'etc': 'make up any key-value pairs'}

  mybsplan = list_scan([glbl.area_det], motor, [1,3,5,7,9], md=mymd) # drives motor to positions 1,3,5,7,9 and fires ``area detector`` at each position
  mybsplan = subs_wrapper(mybsplan, LiveTable([glbl.area_det])) # set up the scan so LiveTable will give updates on how the scan is progressing

Then to use it successfully in xpdAcq you have to do a bit of configuration of global parameters.  This work is done
automatically for you in the ``xpdAcq`` built-in plans.  There are many things you could set up, but the simplest example
is that we want the detector to collect 50 frames each time we fire it, which would give a 50s exposure at a frame-rate of 0.1s (frame-rate
is another ``glbl`` option that you could reset).

.. code-block:: python

  glbl.area_det.images_per_set.put(50)  # set detector to collect 50 frames, so 5 s exposure if continuous acquisition with 0.1s frame-rate

Finally, later on in the experiment when you are ready to run it, you would run this plan just the same as a regular ``ScanPlan`` object!


OK, it is time to :ref:`run our scans <usb_running>`
