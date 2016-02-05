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

*Count scan*

We will set up a Scan-Plan.  typing ``s = Scan?`` returns 

.. code-block:: python

  >>> s = Scan?
  Init signature: Scan(self, scanname, scan_type, scan_params, shutter=True, livetable=True, verify_write=False)
  Docstring:
  metadata container for scan infor

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
  shutter - bool - default=True.  If true shutter will be opened before a scan and
              closed afterwards.  Otherwise control of the shutter is left external.
  livetable - bool - default=True. gives LiveTable output when True, not otherwise
  verify_write - bool - default=False.  This verifies that tiff files have been written
                 for each event.  It introduces a significant overhead.
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


