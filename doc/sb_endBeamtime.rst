.. _sb_endBeamtime:

Finalizing and ending a completed beamtime for a user
-----------------------------------------------------

Required Information
""""""""""""""""""""

  ``PI last name``, ``SAF number`` and ``bt_uid``.
  But xpdAcq will load in information automatically unless user delete ``bt`` object in  ``xpdUser/config_base/yml/``.

Goals of the Process
""""""""""""""""""""

  #. Tar entire xpdUser tree with name ``<PIlastname>_<saf#>_<date>_<bt_uid>.tar``
  #. Place a copy of the tarball into remote archive directory ``pe2_data/.userBeamtimeArchive/``
  #. Verify that the archival copy is present and can be accessed
  #. Delete everything except under ``xpdUser``
  #. Keep operator informed of what is going on

Process Steps
"""""""""""""
  #. Please have a rough idea about the file size of ``xpdUser`` tree. Get this information by right click on ``xpdUser`` folder in file browser.
  #. Type ``_end_beamtime()`` at command prompt. Program will start to archive (uncompressed) entire ``xpdUser``. This process usually takes a while. Please be patient and wait until it's finished
  #. After archiving, program will ask you to check remote copy. Please check if file size to remote copy is roughly as large as the size to local ``xpdUser`` tree.
  #. Now there could be two possibility
    #. **File size and contents of remote copy are confirmed**. Enter ``y`` in the inteactive command prompt then program will flush all directories under ``xpdUser`` and successfully end a beamtime.
    #. **File size or contents to remote copy appear to be inconsistent** with local ``xpdUser`` tree, please answer ``n`` in the interactive command prompt and program will stop at this point. No user data will be removed. Please report a bug on github if this happen.

return to :ref:`bls`
