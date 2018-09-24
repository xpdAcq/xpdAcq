**Added:** None

**Changed:**

* `endbeamtime` process renames the local `xpdUser` to
  `xpdUser_<archive_name>` first before archiving and transferring 
  file to remote location. This is to make sure the next beamtime 
  will not be blocked by the backup process of last beamtime.

**Deprecated:** None

**Removed:** None

**Fixed:** None

**Security:** None
