.. _sb_newBeamtime:

Initializing a new beamtime for a user
--------------------------------------

Required Information
""""""""""""""""""""

 * last name of the PI of the beamtime
 * SAF number

Goals of the Setup
""""""""""""""""""

 1. Ensure that all the information from the previous user has been archived and deleted
 2. Create empty directories with the correct directory structure
 3. Prepopulate the directories with configuration files as needed
 4. Initialize the metadata stack (the list of metadata) with beamtime level information

Setup Steps
"""""""""""

#. [return to this later]
#. We are still finalizing the steps to automate this process. For now:
  
  #. run the start_beamtime script to initialize directories
  #. Ensure that under xpdUsers there are no directories except for Import, Export, tif_base, dark_base, config_base, script_base
  #. Ensure that all those directories are empty.
  #. If you have a .yml file from the user (probably won't yet) place it in the Import directory.
  
  
.. code-block:: python

  >>> import loadsim
  >>> import loadsim
      Traceback (most recent call last):
        File "<pyshell#3>", line 1, in <module>
          import loadsim
        File "c:\users\billinge\documents\github\xpdsim\loadsim.py", line 17, in <module>
          from xpdacq.beamtime import BeamTime
      ImportError: No module named 'xpdacq.beamtime'
 
2. then do it again

::

    >>> print('here')
    here

``icollection`` Typed at the command prompt from any directory.  This starts an ipython session and preloads all the packages needed for XPD data acquisition|

return to :ref:`bls`
