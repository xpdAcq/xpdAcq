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


  .. _auto_dark:

Automated dark collection
"""""""""""""""""""""""""

you might have found something weird when you running a ``prun`` command:

*I only requested one ``prun`` but program runs two scans*

So what happen?

That is actually a feature called auto-dark subtraction of ``xpdAcq``.
When you are running your experiment, ``xpdAcq`` actually checks if you have
collected a **fresh and appropriate** dark frame every time it collects a scan.
The definition of **fresh and appropriate** is:

**Nice and fresh**
^^^^^^^^^^^^^^^^^^

  .. code-block:: none

    Given a certain period T (``dark window``), there exists a dark frame
    with the same **total exposure time** and exactly the same **acquisition time**
    as the light frame we are about collect.

  .. note::

    At **XPD**, area detector is running in ``continuous acquisition`` mode,
    which means detector keeps **reading** but only **saves** image when ``xpdAcq``
    tells it to with desired exposure time. In short,

    * acquisition time defines how fast is detector reading time,
      ranged from 0.1s to 5s.

    * exposure time means total exposure time, which user defined.

  Automated dark collection is enabled by default and it can be turned off by:

  .. code-block:: python

    glbl.auto_dark = False
    glbl.shutter_control = False

  And period of dark window can be modified by:

  .. code-block:: python

    glbl.dk_window = 200 # in minutes. default is 3000 minutes

  Having ``auto_dark`` set to ``True`` is strongly recommended as this enables
  ``xpdAcq`` to do automated dark frame subtraction when you pull out data from
  centralized **NSLSL-II** server.

.. _auto_calib:

Automated calibration capture
"""""""""""""""""""""""""""""

Often times, keeping track with which calibration file is associated with
certain scan is very tiring. ``xpdAcq`` makes this easier for you. Before every
scan is being collected, program goes to grab the most recent calibration
parameters in ``/home/xf28id1/xpdUser/config_base`` and load them as part of
metadata so that you can reference them whenever you want and make in-situ data
reduction possible!

.. _calib_manual:

Quick guide of calibration steps with pyFAI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. First you will see an image window like this:

  .. image:: ./img/calib_05.png
    :width: 400px
    :align: center
    :height: 300px

  That is the image we want to perform azimuthal calibration with. Use magnify
  tool at the tool bar to zoom in and **right click** rings. Starting from
  the first, inner ring and to outer rings. Usually a few rings (~5) should be
  enough.

  .. image:: ./img/calib_07.png
    :width: 400px
    :align: center
    :height: 300px

2. After selecting rings, click on the *original* terminal and hit ``<enter>``.
  Then you will be requested to supply indices of rings you just selected.
  Remember index **starts from 0** as we are using ``python``.
  After supplying all indices, you should have a window to show your calibration:

  .. image:: ./img/calib_08.png
    :width: 400px
    :align: center
    :height: 300px

  Program will ask you if you want to modify parameters, in most of case, you
  don't have to. So just hit ``<enter>`` in the terminal and integration will be
  done.

3. Finally 1D integration and 2D regrouping results will pop out:

  .. image:: ./img/calib_09.png
    :width: 400px
    :align: center
    :height: 300px

  You can qualitatively interrogate your calibration by looking if lines in
  2D regrouping are straight or not.

  After this step, a calibration file with name ``pyFAI_calib.yml`` will be
  saved under ``/home/xf28id1/xpdUser/config_base``

Alright, you are done then! With ```automated calibration capture`` feature, ``xpdAcq``
will load calibration parameters from the most recent config file.

.. _import_sample:

Sample metadata imported from spreadsheet
"""""""""""""""""""""""""""""""""""""""""

In order to facilitate retrospective operation on data, we suggest you to enter
as much information as you can and that is the main philosophy behind ``xpdAcq``.

Typing in sample metadata during beamtime is always less efficient and it wastes
your time so a pre-populated excel sheet with all metadata entered beforehand
turns out to be the solution.

In order import sample metadata from spreadsheet, we would need you to have a
pre-filled spreadsheet with name ``<saf_number>_sample.xls`` sit in ``xpdConfig``
directory. Then the import process is simply:

.. code-block:: python

  import_sample(300564, bt) # SAF number is 300564 to current beamtime
                            # beamtime object , bt, with SAF number 300564 has created
                            # file with 300564_sample.xls exists in ``xpdConfig`` directory


comma separated fields
^^^^^^^^^^^^^^^^^^^^^^

  Files with information entities are separated by a comma ``,``.

  Each separated by ``,`` will be individually searchable later.

  Fields following this parsing rule are:

  ============= ========================================================
  ``cif name``  pointer of potential structures for your sample, if any.
  ``Tags``      any comment you want to put on for this measurement.
  ============= ========================================================

  Example on ``Tags``:

  .. code-block:: none

    background, standard --> background, standard

  And a search on either ``background`` or``standard`` later on will include
  this header.


name fields
^^^^^^^^^^^

  Fields used to store a person's name in ``first name last name`` format.

  Each person's first and last name will be searchable later on.

  Fields following this parsing rule are:

  ======================    =========================================================
  ``Collaborators``         name of your collaborators
  ``Sample Maker``          name of your sample maker
  ``Lead Experimenters``    a person who is going to lead this experiment at beamline
  ======================    =========================================================

  Example on name fields:

  .. code-block:: none

    Maxwell Terban, Benjamin Frandsen ----> Maxwell, Terban, Benjamin, Frandsen

  A search on either ``Maxwell`` or ``Terban`` or ``Benjamin`` or ``Frandsen``
  later will include this header.


phase string
^^^^^^^^^^^^

  Field used to specify the phase information and chemical composition of your
  sample. It's important to enter this field correctly so that we can have
  accelerated data reduction workflow.

  Fields follows this parsing rule are:

  ==============  ==============================================================
  ``Phase Info``  field to specify phase information and chemical composition of
                  your sample
  ==============  ==============================================================

  phase string will be expect to be enter in a form as
  ``phase_1: amount, phase_2: amount``.

  An handy example of 0.9%  sodium chloride water will be:

  .. code-block:: none

    Nacl: 0.09, H20: 0.91

  This ``Phase Info`` will be parsed as:

  .. code-block:: python

    {'sample_composition': {'Na':0.09, 'Cl':0.09, `H`:1.82, `O`:0.91},
     'sample_phase': {'NaCl':0.09, 'H20':0.91},
     'composition_string': 'Na0.09Cl0.09H1.82O0.91'}

  ``composition_string`` is designed for data reduction software going to be
  used. Under ``xpdAcq`` framework, we will assume
  `pdfgetx3 <http://www.diffpy.org/products/pdfgetx3.html>`_

  As before, a search on ``Na`` or ``Cl`` or ``H`` or ``O`` will include this
  header. Also a search on ``Nacl=0.09`` will include this header as well.

.. _background_obj:

Sample objects going to be generated
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Sample**:

  Each row in your spreadsheet will be taken as one valid Sample and metadata
  will be parsed based on the contents you type in with above parsing rule.


* **background**:

  In additional to ``Sample`` objects parsed from rows, ``xpdAcq`` also create
  background objects with information you type in at ``Geometry`` field.

  background objects will automatically tagged as ``is_background`` in metadata.

Generally, after successfully importing sample from spreadsheet, that is what
you would see:

.. code-block:: python

  In [1]: import_sample(300564, bt)
  *** End of import Sample object ***
  Out[1]: <xpdacq.utils.ExceltoYaml at 0x7fae8ab659b0>

  In [2]: bt.list()

  ScanPlans:


  Samples:
  0: P2S
  1: Ni_calibrant
  2: activated_carbon_1
  3: activated_carbon_2
  4: activated_carbon_3
  5: activated_carbon_4
  6: activated_carbon_5
  7: activated_carbon_6
  8: FeF3(4,4-bipyridyl)
  9: Zn_MOF
  ...

  41: ITO_glass_noFilm
  42: ITO_glass_1hrHeatUpTo250C_1hrhold250C_airdry
  43: ITO_glass_1hrHeatUpTo450C_1hrhold450C_airdry
  44: ITO_glass_30minHeatUpTo150C_1.5hrhold150C_airdry
  45: CeO2_film_calibrant
  46: bkg_1mm_OD_capillary
  47: bkg_0.9mm_OD_capillary
  48: bkg_0.5mm_OD_capillary
  49: bkg_film_on_substrate


.. _auto_mask:

Auto-masking
""""""""""""

* auto-masking with user defined beamstop mask


Let's :ref:`take a quick look at our data <usb_quickassess>`
