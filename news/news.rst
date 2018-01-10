**Added:**

* Added news to the repo so we can changelog better

**Changed:**

* Change the filepath structure in ``glbl`` to align with the update
  at XPD. All ``xf28id1`` -> ``xf28id2``, including hostname and
  nfs-mount drives.

**Deprecated:** 

* Remove static mask injection. Mask is now handled by the analysis
  pipeline dynamically.

**Removed:** None

**Fixed:**

* Instruction in ``run_calibration``. There is a specific print statement
  to tell the user to finish the interactive calibration process in the
  analysis terminal.

**Security:** None
