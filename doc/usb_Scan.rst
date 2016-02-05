.. _usb_scan:

Setting up your scan objects
----------------------------

Scan objects (of type ``'sc'`` ) are created just like :ref:`Experiment and Sample <usb_experiment>` objects,
but they serve a slightly different purpose and so we deal with them separately here. To review the syntax
of creating (*instantiating* ) and retrieving (``bt.get()`` ) acquire objects in general, please review
the information :ref:`here <usb_experiment>` and :ref:`here <usb_where>` , respectively.

Firstly, what is a scan?  A scan is a grouped set of detector exposures.  The set may
contain just one exposure (we call that a count scan, ``'ct'`` ).  Or it may be a series of exposures 
taken one after the other, possibly with a delay between.  We
call that a time-series (or ``'tseries'`` ).  Another popular one that is supported is the
a temperature series, or temperature ramp, ``Tramp'``.  More are also on the way, but
these simple scans may also be combined together in scripts, giving the user significant
control over how to construct their experiment.

To run a scan we need a *Scan-Plan* and a *sample*.  The Scan-Plan is the detailed description of
what the scan will do, but it doesn't become a *scan* until it is run on a particular sample.
Separating a scan into a plan and an execution (which is different than how SPEC works
for those old enough) makes it very easy to run a number of different samples with the
exact same scan plan, or (if you really want to) to collect dark images with exactly the same scan pattern, and so on.
We also want to save scan metadata accurately when the scan is actually run.  To ensure
this, each scan object takes the scan parameters and it uses the same parameters
both to run the scan at run-time, and to save them, along with the sample information,
in the metadata for each exposure.

With this in mind, the workflow is that *we never edit a scan and rerun it* (stop that you SPEC people!).
What we do is that we create a new Scan-Plan object, **and give it a different name**,
every time we want to do a different, *even slightly different*, scan.  These are all
saved for reload and will be sent home with you at the end of the experiment.  A word of advice:
come up with your own easy to remember naming scheme. For example, when you create
a ``'ct'`` scan object use the scheme ``'ct<#>'`` where you replace ``<#>`` with the length
of the count in seconds, so a 1.5 second exposure would be named ``'ct1.5'``.  You might
call temperature ramps as ``T``.  These take start temperature, stop temperature and step size,
so a good naming scheme would be ``'T<startT>.<stopT>.<Tstep>'``, e.g., ``'T300.500.10'``.

Setting up ScanPlans
""""""""""""""""""""

Typing ``s = Scan?`` returns 

.. code-block:: python

  >>> s = Scan?
  Init signature: Scan(self, scanname, scan_type, scan_params, shutter=True, livetable=True, verify_write=False)
  Docstring:
  ScanPlan object that defines scans to run.  To run them: prun(Sample,ScanPlan)

  Arguments:
  scanname - string - scan name.  Important as new scans will overwrite older
         scans with the same name.
  scan_type - string - type of scan. allowed values are 'ct','tseries', 'Tramp' 
         where  ct=count, tseries=time series (series of counts),
         and Tramp=Temperature ramp.
  scan_params - dictionary - contains all scan parameters that will be passed
         and used at run-time.  Don't make typos in the dictionary keywords
         or your scans won't work.  The list of allowed keywords is in the 
         documentation, but 'exposure' sets exposure time and is all that is needed
         for a simple count. 'num' and 'delay' are the number of images and the
         delay time between exposures in a tseries.
  shutter - bool - default=True.  If True, in-hutch fast shutter will be opened before a scan and
              closed afterwards.  Otherwise control of the shutter is left external. Set to False
              if you want to control the shutter by hand.
  livetable - bool - default=True. gives LiveTable output when True, not otherwise
  verify_write - bool - default=False.  This verifies that tiff files have been written
                 for each event.  It introduces a significant overhead so mostly used for
                 testing.
  File:           c:\users\billinge\documents\github\xpdacq\xpdacq\beamtime.py
  Type:           type
  
telling what (at the time of writing) the Scan-Plan object needs.  
The ``Init signature`` has exactly the required and optional arguments
that we have to give ``Scan`` (optional arguments have a default value indicated
by the ``=`` sign.  If that argument is not specified it will take the default
value).  The ``Docstring`` field has some more explanation about what these different
arguments are.  The docstring is documentation written in the code itself by the
programmer and may be more or less valuable and accurate (though good programmers
write good Docstrings!).  The ``Init signature`` is absolutely accurate and
up to date, so if they are not 100% in agreement, go with the signature.

The arguments types are given in the Docstring. ``self`` is always ignored, so
the first given argument is ``scanname`` and is a string (make sure to enclose it in 
single or double quotes when you give it, i.e., ``'myscan'`` or ``"myscan"`` will 
work but ``myscan`` will not).  The second argument is a string that denotes the scan type. At the time
or writing the only ones available are 'ct', 'tseries' and 'Tramp'.  If you give
any other string values the ScanPlan will be created no problem, but it
will not run if you try it!  The third and last given required-argument is ``scan_params``
and is a dictionary that contains one or more key:value pairs.  In this case
the keys are fixed quantities, and the required keys depends on the scan-type.  Please see
the examples below.  The values are the values of those parameters that you want
for your particular scan-plan.  Python dictionaries are written in the form ``{key1:value1,key2:value2,....,lastkey:lastvalue}``

*Count scan*

Here are some examples of valid count-type ScanPlan definitions:

.. code-block:: python

  >>> sc = Scan('ct1.5','ct',{'exposure':1.5})                      # the simplest count scan definition
  >>> sc = Scan('ct1.5_nosh','ct',{'exposure':1.5},shutter=False)   # same scan as before but let's do the shutter by hand (be careful!)
  >>> sc = Scan('ct100.5_nolt','ct',{'exposure':100.5},livetable=False)    # nice long scan but we don't want to clutter our terminal with the table showing the counts
  >>> sc = Scan('ct2_vw','ct',{'exposure':2},verify_write=True)     # we want to be sure the tiff was written in pe1_data, but pay a price of a ~ 1 second overhead.
  >>> sc = Scan('ct2_vw_nosh','ct',{'exposure':2},verify_write=True,shutter=False) # hopefully you are getting the idea.
  >>> Scan('ct2','ct',{'exposure':2})                               # this will also work in xpdAcq because we can reference this object with bt.list() and bt.get()

A few things to note:

 * Because all these are count ScanPlans, the second argument is ``'ct'`` for all of them.
 * **They all have different names** (the first argument!).  This is necessary in xpdAcq!  On a side note, though it is not OK in Python in general, it is OK for you to make the assignment ``sc = ...`` the same in each case. This would be bad in regular python programming because you would be repeatedly reassigning the same python object (``sc``) with different definitions and they will all be lost except the most recent definition.  However, in xpdAcq we should always reference our objects using ``bt.list()`` then ``bt.get()`` (:ref:`remember? <usb_where>`).  This means that the objects instantiated this way are all saved correctly even with the same assignment, *as long as they have different names*. We can even do some Python insanity such as the last ScanPlan definition shown in the examples.  This object is created with no assignment so there is no way for Python to reference it, but we can in xpdAcq with ``bt.list()`` and ``bt.get()``.
 * It is quite possible to successfully define an incorrectly composed ScanPlan object. You will only know this when you try and run it.  later we will give tools that can validate your scan objects for you, but for now you have to do it by hand.  You can do this by running them in ``dryrun()``, see :ref:`usb_running`.
 * The scan_params syntax is a bit clunky and delicate.  Please just be careful for now.  Later we will give helper functions and maybe a GUI (if we can get funding for a summer student).  Let's all pray to the funding gods!
