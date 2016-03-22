.. _sb_newBeamtime:

Initializing a new beamtime for a user
--------------------------------------

Goals of the Setup
""""""""""""""""""

 1. Ensure that all the information from the previous user has been archived and deleted
 2. Create empty directories with the correct directory structure
 3. Prepopulate the directories with configuration files as needed
 4. Initialize the metadata stack (the list of metadata) with beamtime level information

Setup
"""""

#. **Prepare beamtime config files:** 
   This may be done at the beginning of the cycle or whenever the info from PASS is available.  Just leave multiple ``yml`` files in the ``~/xpdConfig`` directory each with a different saf-number, one for each beamtime. In the future, this step will be replaced with something where the information is obtained directly from the PASS database....that is the plan...
      #. look in ``~/xpdConfig`` for a file called ``saf123.yml``
      #. this is a template.  Make a copy with a new name ``saf<saf number>.yml`` where you replace ``<saf number>`` with the SAF number, e.g., ``saf300456.yml``.
      #. edit the file with the actual information, such as "PI last name", "experimenter list", and so on, following the template.
      #. make sure the final version is saved back into ``~/xpdConfig`` with the correct name (``xpdAcq`` will use this standard naming scheme to search for the config files).
#. **New user will show up tomorrow or today:**
   On xpd computer,
      #. type ``icollection`` to start the ``(collection)`` environment and get the ``In[1]:`` prompt.
      #. type ``bt = _start_collection(<saf_number>)``
         e.g., ``bt = _start_collection(300456)``
      #. there will be two possible outcomes
          #. the environment has already been cleaned from the previous user and there will be no error message
          #. the previous beamtime has not been properly ended (or testing took place in between, whatever).  Then the program will exit asking you to run ``_end_beamtime()``
#. **if (2.3) results in outcome 2.:** 
      #. still in the ``(collection)`` environment, type ``_end_beamtime()`` and follow the prompts.
      #. rerun the start-beamtime sequence => ``bt = _start_beamtime(<saf number>)``.  this time it should result in outcome 1.
#. **Wavelength calibration:**
      #. Do what you have to do to do a wavelength calibration.  Write the wavelength on a bit of paper.
      #. in ``(collection)`` type ``bt.set_wavelength(<wavelength>)``,
         e.g., ``bt.set_wavelength(0.18448)``
#. [not implemented yet].  If the users have provided you with yaml files containing their pre-prepared beamtime objects:
      #. copy them to the directory ``~/xpdUser/config_base/yml``.  They can be in the form of a series of ``yml`` files, or they may by a ``tar`` or ``tar.gz`` file.
      #. type ``bt.import_objects()``
#. At this point, you can hand off to the users.  However, to give the users a better experience, the next step is to do a detector geometry calibration.  If you do this the calibration information will be saved in each data-file allowing automated integration [not yet implemented]
      #. load the desired calibration sample and open the shutter
      #. [not implemented yet] type ``calibration(<calibrant sample object>, <desired count object>)``
for now,
      #. [not implemented yet]find the sample object for your calibrant sample in ``bt.list()`` or create it if it is not there. 
      #. type ``bt.list()``. Find the index number of your desired count-length (preloaded defaults are 0.1s, 0.5s, 1s, 5s, 10s, 30s [fixme]). e.g., I think 'ct30s' is index 10
      #. type ``prun(<sample object>,<scan object>)``, e.g., ``prun(bt.get(2),bt.get(10))`` where index 2 in the object list is the lazy-user sample and index 10 is the 30s count scan (pls check though)
      #. when complete, type ``save_last_tiff()`` to save it as a tiff image.  It should reside in ``~/xpdUser/tiff_base``. 
      #. load it in ``xPDFsuite`` or ``Fit2D`` and do the calibration
      #. save the resulting calibration config file in ``~/xpdUser/config_base`` (note, it goes in config_base, not in ``config_base/yml`` with the (default) file extension ``.cfg``)


return to :ref:`bls`
