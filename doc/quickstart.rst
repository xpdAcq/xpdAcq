.. _qs:

Quick start
-----------

Checklist
+++++++++

The instrument scientist (IS) should have set up your beamtime hardware and software
for you.  Let's check if it is the case.

1. Activate the XPD data acquisition environment:

  * In a terminal look to see if it is already activated.  If it is, you should see ``(collection)`` at the beginning of the line.

  .. code-block:: none

    (collection)xf28id1@xf28id1-ws2:~$

  * If you don't see it, type ``icollection`` at the command prompt then check again.

2. OK, you are in.  Make sure that that the instrument scientist has initiated your beamtime. type ``bt.md`` and hit return. You should see the beamtime (``bt``) metadata (``md``) that has been pre-stored by the IS, and it should contain things like the last name of the PI on the proposal and the SAF number for the beamtime.  If not, please seek out the IS to get your session initialized.
3. Check that the wavelength has been set.  Does the correct x-ray wavelength appear in ``bt.md`` ``['bt_wavelength']`` field, or does it say ``None``.  If the latter, you can still collect scans but automated data reduction may not work, so best to grab the IS again.
5. Check that the Perkin Elmer detector is correctly set up.

  * Look at the Perkin Elmer screen on the CSS and make sure that ``Acquire`` mode has been enabled. If Acquire mode is enabled, it should show system information ``Collecting`` in yellow color. If it hasn't been activated, please click 'start' button.

  .. image:: /cropped_pe1c_ioc.png
    :width: 300px
    :align: center
    :height: 200px

  * Type ``glbl.area_det`` and return.  It should return:

   .. code-block:: python

     In [5]: glbl.area_det
     Out[5]: PerkinElmerContinuous(prefix='XF:28IDC-ES:1{Det:PE1}', name='pe1', read_attrs=['tiff', 'stats1'], configuration_attrs=['images_per_set', 'number_of_sets'], monitor_attrs=[])

There are other setups that you can do to make your experiment run smoothly.  For example, by carrying out a calibration before you start collecting it greatly facilitate data reduction later.  Please talk to the IS if you don't know how to do this.  

But you seem to be set up ok, so let's go and collect some data.

Collecting Data Quickstart
++++++++++++++++++++++++++

The basic way to collect data is to carry out a "scan", by typing the kind of scan and giving it as arguments a ``sample-object`` and a ``scanplan-object``.  These objects just contain information that will either be used to run the scan, and/or just saved as metadata with the data, allowing you to find the data later and process it. You will make your own objects later, but for now you can do a quick scan just to collect some data with some predefined objects.

 1. Type ``bt.list()`` and return.  You should see a list of already defined objects and their index, or the number they sit in the list.
 2. To run a scan you type ``<scan-name>(<sample-object>,<scanplan-object>)``:

   Replace those words in angle brackets with pointers to real objects, eg.:

   1. ``prun(bt.get(2),bt.get(5))`` will do a scan on the dummy sample (``'sa'``) called ``'l-user'``--(for lazy user!) which is in position (index) ``2`` in the ``bt.list()`` list--for 1 second (the name of that object in the list at position ``5`` is ``'ct1s'`` which stands for "count 1 second").
   2. ``prun(bt.get(2),bt.get(7))`` will do a scan for 10 s on the same sample (to see that, look at the list produced by typing ``bt.list()``.
   3. ``setupscan(bt.get(2),bt.get(7))`` will do a setupscan on that sample for 10 seconds.  A setupscan is like a prun ("production run") except it is tagged in metadata as a setupscan so you can separate later which were production runs and which were setup-scans.

   .. code-block:: python
   
     Pro-Tip:
     '''``prun`` and all the scans support different ways of assigning acquire objects. 
     You can either get the objects with the ``bt.get()`` methods as above, or
     to save typing, the scan functions allow you to specify just the object index, 
     or (unique) name of the acquire object. The following expressions are all 
     equivalent:'''

     prun(bt.get(2), bt.get(5))  
     prun('l-user', bt.get(5))
     prun(bt.get(2), 'ct1s')
     prun(2,5)
     prun('l-user','ct1s')


 3. to see the data you have to extract it from the NSLS-ii database.

   1. Type ``save_last_tiff()`` to get the most recent scan you ran.  A dark-subtracted tiff file will appear in the directory ``~/xpdUser/tiff_base`` with prefix ``sub_`` in file name.
   2. ``save_tiff(db[-2])`` gets you the second to last scan that was collected, ``save_tiff(db[-10:])`` gets you the last 10 scans, (the syntax is Pythonic but it means "the items in the list from 10 ago up to the end of the list, i.e., now".  You can do all kinds of slicing and dicing, for example ``db[-10:-8,-2]`` would return the scans that were tenth, ninth and eighth ago, and also the last but one.) and so on.
   3. The tiff file appears in the directory ``~/xpdUser/tiff_base`` with a reasonably recognizable automatically generated name and you can do pretty much what you like with it. For example, copy it to an external drive.  However, there are handy tools on the XPD computer for analyzing your data.  As long as you save all your work in the ``xpdUser`` directory tree (make as many directories as you like under there) your work will be archived in a remote location at the end of your beamtime, and then completely deleted from the local XPD computer so that the next user has their own fresh environment to work in, but your work is safe.
   4. To use data analysis tools on the XPD computer, **in a new terminal window**

     * Type ``getxgui``
     * proceed to :ref:`xPDFsuite_manual`

Remember!
+++++++++
   1. ``bt.list()`` to see what objects are available
   2. ``setupscan(<index-of-Sample-object>,<index-of-ScanPlan-object>)``  to run setup scans until you are ready for production runs, then
   3. ``prun(<index-of-Sample-object>),<index-of-ScanPlan-object>)``
   4. ``save_tiff(db[list_of_scans])`` to get the data back as a tiff file
   5. ``getxgui`` (xPDFsuite) to visualize it, integrate it to 1D and process to get a diffraction pattern or PDF.

Next Steps
++++++++++

So you have collected some data, and looked at it.  It is probably time to set up some more extensive data-objects so that you will be able to search easily for your data later and do more sophisticated scans.
Please take the time to read the full documentation from **XPD user** section to get the most out of your data.  But for now, here is a quick summary.

You should try and set up some of your own scanplan objects:
  * let's say you want to do a count scan for 1.5 minutes.

    1. type ``bt.list('sp')``  to see the current list of scanplan objects
    2. make a new ``scanPlan`` object by typing

      .. code-block:: python

        >>> ScanPlan('ct_90')

      This will create a ``'ct'``, or count-type, scan with an exposure of 90 s or 1.5 minutes.
      To find more details on creating new ``ScanPlan`` objects, please see :ref:`usb_Scan`
    3. type ``bt.list('sp')`` again.  You should see your new ``ScanPlan`` object at the end of the list.  You can now use your object to collect data by passing it to a "scan" function:
    4. You can run it using ``prun(<sample-object>,<index-of-your-new-ScanPlan-Object>)``  If your new object is at position 11 in the list, and position 2 holds a ``Sample`` object (it does by default) then ``prun(2,11)``, or probably better, ``setupscan(2,11)`` since we are still messing around here.

Types of scan available.
  They all take as arguments ``(<sample-object>, <scanplan-object>)`` in that order:

  1. ``prun()`` - the one you will use the most.  It stands for "production run"
  2. ``setupscan()`` - it is just the same as ``prun()`` but the data are tagged as being test/setup data, helping you to keep track of what is what later.
  3. ``dryrun()`` - it doesn't execute anything, only prints out metadata, so you can test out your scan to see what it will do.
  4. ``background()`` - Like ``prun()`` but it tags the dataset as a background scan, so later you can search for all your background scans!
  
  these ones you will use less often, if at all
  
  5. ``calibration()`` - the same as ``prun()`` , but the data are tagged as calibration data.
  6. ``dark()`` - you shouldn't have to use this as dark scans (shutter closed) and dark subtractions of your data are done automatically, but it is here in case you do it is there.  It ensure the shutter is closed and tags the scan as being a dark.

Types of ScanPlan objects available:
  * ``'ct'`` just exposes the the detector for a number of seconds. e.g.,  ``ScanPlan('ct17.5s','ct',{'exposure':17.5})``, or ``ScanPlan('ct_17.5')`` for short, is a scan plan that just exposes the detector for 17.5 seconds.
  * ``'tseries'`` executes a series of ``'num'`` exposures, each of exposure time ``'exposure'`` seconds with  a delay of ``'delay'`` seconds between them.  e.g., ``ScanPlan('tseries_1_59_50','tseries',{'num':50,'exposure':1,'delay':59})``, or ``ScanPlan('tseries_1_59_50')`` for short, will measure 50 scans of 1 second with a delay of 59 seconds in between each of them.
  * ``'Tramp'`` executes a temperature ramp from ``'startingT'`` to ``'endingT'`` in temperature steps of ``'Tstep'`` with exposure time of ``'exposure'``.  e.g., ``ScanPlan('Tramp_1_200_500_5','Tramp',{'startingT':200, 'endingT':500, 'Tstep':5, 'exposure':1})``, or ``ScanPlan('Tramp_1_200_500_5')`` for short, will automatically change the temperature, starting at 200 K and ending at 500 K, measuring a scan of 1 s at every 5 K step. The temperature controller will hold at each temperature until the temperature stabilizes before starting the measurement.
  in the shortened "auto-naming" syntax, the logic is that the first number is always the exposure time.  Later numbers depend on the type of the ``ScanPlan`` type.  Remember, you can always give your object to ``dryrun()`` and it will tell you what Frankenstein you created without executing anything.
 
Types of Sample objects available:
  * ``Sample`` - there is only one type of Sample "object", but you will create as many copies of it as you have samples, each with a unique sample name that helps you remember what the sample is.  It is a container for all the metadata about your sample, and moving forward, the metadata may be used for automated data reduction and modeling.
    
Here is a summary table:

=========== =================================================================================================== =================================
ScanPlan    Syntax                                                                                              Short Form
=========== =================================================================================================== =================================
``ct``      ``ScanPlan('ct17.5','ct',{'exposure':17.5})``                                                       ``ScanPlan('ct_17.5')``
``tseries`` ``ScanPlan('tseries_1_59_50','tseries',{'num':50,'exposure':1,'delay':59})``                        ``ScanPlan('tseries_1_59_50')``
``Tramp``   ``ScanPlan('Tramp_1_200_500_5','Tramp',{'startingT':200, 'endingT':500, 'Tstep':5, 'exposure':1})`` ``ScanPlan('Tramp_1_200_500_5')``
=========== =================================================================================================== =================================

Abort!
++++++

  Oops, you requested a scan with the wrong ``Sample``, or ``ScanPlan`` object, or your ``ScanPlan`` object is not doing what you expected!!!!!

      .. code-block:: python

        >>> CTL-C
        
  will interrupt your scan and allow you to choose whether to abort it, or restart it.  
  * If you abort it the system is reset to where it was before the scan started.

Experiment and sample objects:
  1. It is time well spent to set up all your experiment and sample objects accurately.
  To set up a sample you have to give it an experiment object, so ``Sample('Li battery electrode',bt.get(96))`` uses the object in ``bt.list(96)`` which must be an ``ex`` type object, for example I #may have made# it with ``Experiment('cycled and uncycled batteries',bt)``.
  The ``bt`` is the beamtime object. For complete documentation, please see :ref:`usb_experiment`

  2. It is also possible to download xpdAcq `from here <https://github.com/xpdAcq/xpdAcq>`_ and run it on your own computer to set up the ``sample`` and ``scanplan`` objects you think you will need at the beamtime.
  So when you are at XPD you can concentrate on collecting data and not typing metadata.
  Simulation at home is strongly recommended. See the full documentation for more details at here [FIXME doc needed]

User scripts:
+++++++++++++

  Your ``scanplan`` objects can be sequenced into scripts, executing one after the other as you desire.  To set this up, write a sequence of commands into a text file, save it with the extension ``.py`` in the ``userScripts`` directory with a memorable name, like ``myNightShiftScript.py``.  Double and triple check your script, then when you are ready to execute it, in ``ipython`` session type:

  .. code-block:: python

    %run -i ~/xpdUser/userScripts/myNightShiftScript.py

  Stay there for a while to make sure everything is running as expected and go to bed!

There is much more to the ``xpdAcq`` software that will give you superpowers in rapid and flexible data collection, data retrieval and processing.
This was just the quick start, but much more information is in the full documentation at **XPD user** section

Code Sample
+++++++++++

Here is a sample code covering the entire process from defining ``Experiment``,
``Sample`` and ``ScanPlan`` objects to running ``ScanPlans`` with different kinds of ``run``.
Please replace the name and parameters in each function depending your need.

**Tip**: copy-and-paste is *always* your good friend

.. code-block:: python


  # bt list method to see objects we have
  bt.list()

  # define acquire objects
  ex = Experiment('xpdAcq_test', bt)
  sa = Sample('xpdAcq_test_Sample', ex)

  # define "ct" scanplan with exp = 0.5
  ct = ScanPlan('xpdAcq_test_ct','ct',{'exposure':0.5})

  # define "TrampUp" scanplan with exp = 0.5, startingT = 300, endingT = 310, Tstep = 2
  # define "TrampDown" scanplan with exp = 0.5, startingT = 310, endingT = 300, Tstep = 2
  TrampUp = ScanPlan('xpdAcq_test_Tramp','Tramp',{'exposure':0.5, 'startingT': 300, 'endingT': 310, 'Tstep':2})
  TrampDown = ScanPlan('xpdAcq_test_Tramp','Tramp',{'exposure':0.5, 'startingT': 310, 'endingT': 300, 'Tstep':2})

  # define "time series" scanplan with exp = 0.5, num=10, delay = 2
  tseries = ScanPlan('xpdAcq_test_tseries', 'tseries', {'exposure':0.5, 'num':5, 'delay':2})


  # Frist, let use dryrun with different ScanPlans to have a preview on scan metadata
  dryrun(sa, ct)

  # Then let's do calibration run and save the image in order to open it in calibration software
  calibration(sa, ct)
  save_last_tiff()

  # Use setupscan to check image quality under current scan parameters
  setupscan(sa, ct)
  save_last_tiff()

  # Everything looks right. Let's do prun with different ScanPlans and save the tiffs
  prun(sa, ct)
  save_last_tiff() # save tiffs from last scan
  prun(sa, TrampUp)
  prun(sa, TrampDow)
  prun(sa, tseries)
  save_tiff(db[-3:]) # save tiffs from last three scans
