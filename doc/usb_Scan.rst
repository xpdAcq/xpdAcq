.. _usb_scan:

ScanPlan objects
----------------

ScanPlan objects (of type ``'sp'`` ) are created just like :ref:`Experiment and Sample <usb_experiment>` objects,
but they serve a slightly different purpose and so we deal with them separately here. To review the syntax
of creating (*instantiating* ) and retrieving (``bt.get()`` ) acquire objects in general, please review
the information :ref:`here <usb_experiment>` and :ref:`here <usb_where>` , respectively.

Firstly, what is a scanplan?  A scanplan is a grouped set of detector exposures.  The set may
contain just one exposure (we call that a count scan, ``'ct'`` ).  Or it may be a series of exposures
taken one after the other, possibly with a delay between.  We
call that a time-series (or ``'tseries'`` ).  Another popular one that is supported is the
a temperature series, or temperature ramp, ``'Tramp'``.  More are also on the way, but
these simple scanplans may also be combined together in scripts, giving the user significant
control over how to construct their experiment.

To run a scan we need a *ScanPlan* and a *Sample*.  The ScanPlan is the detailed description of
what the scan will do, but it doesn't generate any *scan* until it is run on a particular sample.
Separating a scan into a plan and an execution (which is different than how SPEC works
for those old enough) makes it very easy to run a number of different samples with the
exact same scanplan, or (if you really want to) to collect dark images with exactly the same scan pattern, and so on.
We also want to save scan metadata accurately when the scan is actually run.  To ensure
this, each scan object takes the scanplan parameters and it uses the same parameters
both to run the scan at run-time, and to save them, along with the sample information,
in the metadata for each exposure.

With this in mind, the workflow is that *we never edit a scanplan and rerun it* (stop that you SPEC people!).
What we do is that we create a new ScanPlan object, **and give it a different name**,
every time we want to do a different, *even slightly different*, scan. These are all
saved for reload and will be sent home with you at the end of the experiment.  A word of advice:
come up with your own easy to remember naming scheme. For example, when you create
a ``'ct'`` scan object use the scheme ``'ct<#>'`` where you replace ``<#>`` with the length
of the count in seconds, so a 1.5 second exposure would be named ``'ct1.5'``.  You might
call temperature ramps as ``T``.  These take start temperature, stop temperature and step size,
so a good naming scheme would be ``'T<startT>.<stopT>.<Tstep>'``, e.g., ``'T300.500.10'``.

Setting up ScanPlans
""""""""""""""""""""

Typing ``s = ScanPlan?`` returns

.. autofunction:: xpdacq.beamtime.ScanPlan

telling what (at the time of writing) the ScanPlan object needs.
The ``Init signature`` has exactly the required and optional arguments
that we have to give ``Scan`` (optional arguments have a default value indicated
by the ``=`` sign.  If that argument is not specified it will take the default
value).  The ``Docstring`` field has some more explanation about what these different
arguments are.  The docstring is documentation written in the code itself by the
programmer and may be more or less valuable and accurate (though good programmers
write good Docstrings!).  The ``Init signature`` is absolutely accurate and
up to date, so if they are not 100% in agreement, go with the signature.

The argument types are given in the Docstring. ``self`` is always ignored, so
the first given argument is ``scanname`` and is a string (make sure to enclose strings in
single or double quotes when you give it, i.e., ``'myscan'`` or ``"myscan"`` will
work but ``myscan`` will not).  The second argument is a string that denotes the scan type. At the time
or writing the only ones available are ``'ct'``, ``'tseries'`` and ``'Tramp'``.  If you give
any other string values the ScanPlan will be created no problem, but it
will not run if you try it!  The third and last given required-argument is ``scan_params``
and is a dictionary that contains one or more key:value pairs.  In this case
the "keys" are fixed quantities, where the required keys depends on the scan-type.  Please see
the examples below.  The "values" are the values of those parameters that you want
for your particular scan-plan.  Python dictionaries are written in the form ``{key1:value1,key2:value2,....,lastkey:lastvalue}``

*Count scan*

Here are some examples of valid count-type ScanPlan definitions:

.. code-block:: python

  >>> sc = ScanPlan('ct_1.5','ct',{'exposure':1.5})                      # the simplest count scan definition
  >>> sc = ScanPlan('ct_1.5','ct',{'exposure':1.5},shutter=False)   # same scan as before but let's do the shutter by hand (be careful!)
  >>> sc = ScanPlan('ct_100.5','ct',{'exposure':100.5},livetable=False)    # nice long scan but we don't want to clutter our terminal with the table showing the counts
  >>> sc = ScanPlan('ct_2','ct',{'exposure':2},verify_write=True)     # we want to be sure the tiff was written in pe1_data, but pay a price of a ~ 1 second overhead.
  >>> sc = ScanPlan('ct_2','ct',{'exposure':2},verify_write=True,shutter=False) # hopefully you are getting the idea.
  >>> ScanPlan('ct_2','ct',{'exposure':2})                               # this will also work in xpdAcq because we can reference this object with bt.list() and bt.get()

A few things to note:

 * Because all these are count ScanPlans, the second argument is ``'ct'`` for all of them.
 * **They all have different names** (the first argument!).  This is necessary in xpdAcq!  On a side note, though it is not OK in Python in general, in xpdAcq it *is* OK for you to make the assignment (i.e., ``sc = ...``) the same in each case. This would be bad in regular python programming because you would be repeatedly reassigning the same python object (``sc``) with different definitions and they will all be lost except the most recent definition.  However, in xpdAcq we should always reference our objects using ``bt.list()`` then ``bt.get()`` (:ref:`remember? <usb_where>`).  This means that the objects instantiated this way are all saved correctly even with the same assignment, *as long as they have different names*. We can even do some Python insanity such as the last ScanPlan definition shown in the examples.  This object is created with no assignment so there is no way for Python to reference it, but we can in xpdAcq with ``bt.list()`` and ``bt.get()``.
 * It is quite possible to successfully define an incorrectly composed ScanPlan object but we have tools that can validate your ``ScanPlan`` objects by the time of instantiation. Validator will tell you which filelds are missing through a warning, please follow the instruction from warning message and modify your code. You can run your ScanPlan and Sample object with ``dryrun()`` to have a look on how your metadata will be recorded. See :ref:`usb_running`.
 * The scan_params syntax is a bit clunky and delicate.  Please just be careful for now.  Later we will give helper functions and maybe a GUI (if we can get funding for a summer student).  Let's all pray to the funding gods!

OK, it is time to :ref:`run our scans <usb_running>`
