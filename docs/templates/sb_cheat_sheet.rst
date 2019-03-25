.. _sb_cheat_sheet:

Cheat Sheet
===========

Please use this page as a reminder and to copy  and paste code snippets into your ``collection-yyQn.x``
and ``analysis`` ipython terminals.

To understand in more detail what the code does, please go to :ref:`xpdu`

Start a beamtime
----------------

1. run ``xpdui`` to start a collection ipython environment
2. run the end-beamtime sequence if it has not been run

.. code-block:: python

  bt = _end_beamtime()

3. run the start-beamtime sequence

.. code-block:: python

  bt = _start_beamtime(PI_last=<last_name_of_pi_on_the_SAF>, saf_num=<saf_number>,
                       experimenters = ['Emma', 'Watson', 'Tim', 'Liu'],
                       wavelength=0.184649)

``xpdAcq`` will raise an error if a user inadvertently attempts to start a new beatime in previous ``python`` session. 

If you receive this ``xpdAcqError`` message,

.. code-block:: python

  It appears that end_beamtime may have been run. 
  If you wish to start a new beamtime, 
  please open a new terminal and proceed with the standard starting sequence

please open a new terminal, type in ``bsui`` to enter a fresh collection enviornment (``ipython session``) and start beamtime again.


4. link bt to xrun

.. code-block:: python

  xrun.beamtime = bt

5. Copy the Excel spreadsheet provided by the experimenters with their samples in it to the ``xpdUser/import`` directory. Check that it has the name ``<saf_number>_samples.xlsx``
where the <saf_number> must match that of the current beamtime.  If the user didn't supply such a thing, then copy the file ``300000_samples.xls`` from the ``xpdConfig`` directory
(which is at the same level of the directory tree as the ``xpdUser`` directory) to ``xpdUser/import`` and edit the filename so that it has the ``saf_number`` of the current beamtime.

6. load the info in the spreadsheet by typing:

.. code-block:: python

  import_sample_info()

.. Note::

  The sample objects may be updated at any time by editing the spreadsheet in the ``xpdUser/import`` directory
  and rerunning ``load_sample_info()``

8. calibrate the wavelength.

   FIXME

Things should now be set up for the user to run the experiment.  Information about this is in
the main part of the documentation.
