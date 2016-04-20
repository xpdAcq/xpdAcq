.. _sb_endBeamtime:

Finalizing and ending a completed beamtime for a user
-----------------------------------------------------

Required Information
""""""""""""""""""""

``PI last name``, ``SAF number`` and ``bt_uid``. But xpdAcq will load in information automatically unless user delete ``bt`` object in  ``xpdUser/config_base/yml/``.

Goals of the Process
""""""""""""""""""""

 1. Tar entire xpdUser tree with name ``<PIlastname>_<saf#>_<date>_<bt_uid>.tar``
 3. Place a copy of the tarball into remote archive directory ``pe2_data/.userBeamtimeArchive/``
 4. Verify that the archival copy is present and can be accessed
 5. Delete everything except under ``xpdUser``
 6. Keep operator informed of what is going on
 
Process Steps
"""""""""""""
  1. First check roughly how large is ``xpdUser``
  2. type ``_end_beamtime()`` at command prompt. Program will start to archive (uncompressed) entire ``xpdUser``. This process usually takes a while. Please be patient and wait untill it's finished
  3. After archiving, program will ask you to check remote copy. Please check if file size to remote copy is roughly as large as the size to local ``xpdUser`` tree.
  4.1 Once 3 is confirmed, answer ``y`` then program will flush all directories under ``xpdUser`` and successfully end a beamtime.
  4.2 If file size to remote copy appears to be inconsistent with local ``xpdUser`` tree, please answer ``n`` and program will stop at this point. No user data will be removed.

return to :ref:`bls`
