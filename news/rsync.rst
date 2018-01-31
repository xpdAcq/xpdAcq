**Added:** None

**Changed:** None

**Deprecated:**

* Replace most ``shutil`` functionalities with native unix commands
  called by ``subprocess`` to have a clear picture on the system response.

**Removed:** None

**Fixed:**

* Add ``--timeout`` option to rsync during ``end_beamtime`` to take care of (periodic) delay in nils-ii network.

**Security:** None
