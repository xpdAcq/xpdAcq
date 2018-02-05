**Added:** None

**Changed:** None

**Deprecated:**

* Replace most ``shutil`` functionalities with native Unix commands
  called by ``subprocess`` to have a clear picture on the system response.

**Removed:** None

**Fixed:**

* Add ``--timeout`` option to rsync during ``_end_beamtime`` to allow 
  temporally disconnect.

* Exclude hidden files from the ``_end_beamtime`` archival. Those files 
  are mainly used as configurations by local applications and are less 
  likely to be reusable even if user requests them.


**Security:** None
