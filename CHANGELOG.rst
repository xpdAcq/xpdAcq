=================
xpdAcq Change Log
=================

.. current developments

v0.7.0
====================

**Added:**

None

* Filter positions are recorded in metadata on each xrun.
* Added verification step: Beamline scientists must verify longterm beamline config file at the start of a new beamtime.

* Automatically display current filter positions (``In`` or ``Out``) from for every ``xrun``.


**Changed:**

* Change the filepath structure in ``glbl`` to align with the update
  at XPD. All ``xf28id1`` -> ``xf28id2``, including hostname and
  nfs-mount drives.


**Deprecated:**

* Remove static mask injection. Mask is now handled by the analysis
  pipeline dynamically.


**Fixed:**

* Instruction in ``run_calibration``. There is a specific print statement
  to tell the user to finish the interactive calibration process in the
  analysis terminal.

* Fix ``_end_beamtime``. Details about the fixes are:

  * Use rsync while archiving ``xpdUser`` so that user can see 
    the progress. (rsync lists files have been transferred)

  * More sophisticated logic when flushing xpdUser directory. 
    Now the function will tell the user to close files used by 
    the current process, instead of throwing an error and failing 
    the process.

  * Some cleaning in the logic. Program will remove the remote 
    archive if user doesn't confirm to flush the local directory 
    so that we could potentially avoid having multiple copies at 
    the remote location.




