.. _sb_newBeamtime:

Initializing a new beamtime for a user
--------------------------------------

Goals of the Setup
""""""""""""""""""

 1. Ensure that all the information from the previous user has been archived and deleted
 2. Create empty directories with the correct directory structure
 3. Prepopulate the directories with configuration files as needed
 4. Initialize the metadata stack (the list of metadata) with beamtime level information
 5. Make certain that the proxy is running see the
`proxy documentation in bluesky <http://nsls-ii.github.io/bluesky/callbacks.html#minimal-example>`_ (make certain ``bluesky-0MQ-proxy 5577 5578`` is running)

Setup
"""""

#. **New user will show up tomorrow or today:**

  On XPD computer,
    #. type ``icollection`` to start the ``(collection)`` environment and get the ``In[1]:`` prompt.
    #. type ``bt = _start_collection(<PI_last>, <saf_number>, <experimenter_list>, <wavelength>)`` for example,

      .. code-block:: python

        ``bt = _start_beamtime('Billinge', 300564, ['Tim', 'Liu'], wavelength=0.1832)

  there will be two possible outcomes
    #. **outcome 1**: the environment has already been cleaned from the previous user and there will be no error message

    #. **outcome 2**: the previous beamtime has not been properly ended (or testing took place in between, whatever).
      Then the program will exit asking you to run ``_end_beamtime()``

  **if results in outcome 2.:**
    #. still in the ``(collection)`` environment, type ``_end_beamtime()`` and follow the prompts.
    #. rerun the start-beamtime sequence, ``bt = _start_collection(<PI_last>, <saf_number>, <experimenter_list>, <wavelength>)``  this time it should result in outcome 1.

#. **Wavelength calibration:**
    #. Do what you have to do to do a wavelength calibration. Write the wavelength on a bit of paper.
    #. in ``(collection)`` type ``bt.wavelength = <new_value>``.  e.g., ``bt.wavelength = 0.18448``

#. Copy the Excel spreadsheet provided by the experimenters with their samples in it to the ``xpdUser/import`` directory. Check that it has the name ``<saf_number>_samples.xlsx``
  where the <saf_number> must match that of the current beamtime.  If the user didn't supply such a thing, then copy the file ``300000_samples.xls`` from the ``xpdConfig`` directory
  (which is at the same level of the directory tree as the ``xpdUser`` directory) to ``xpdUser/import`` and edit the filename so that it has the ``saf_number`` of the current beamtime.

#. If the users have provided you with yaml files containing their pre-prepared helper objects:
      #. copy them to the directory ``~/xpdUser/Import``.  They can be in the form of a series of ``.yml``, ``.py`` ``.npy`` files,
      or they may be a bundle of them in ``.tar``, ``.zip`` or ``tar.gz`` file
      #. type ``import_userScriptsEtc()`` and files with supported format will be imported and placed in the right places.

#. At this point, you can hand off to the users.  However, to give the users a better experience, the next step is to do a detector geometry calibration.  If you do this the calibration information will be saved in each data-file allowing automated integration.
      #. put in beam attenuator
      #. mount Ni onto diffractometer
      #. type ``run_calibration()``
      #. follow :ref:`calib_manual`
