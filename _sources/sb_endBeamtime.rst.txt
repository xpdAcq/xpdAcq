.. _sb_endBeamtime:

Finalizing and ending a completed beamtime for a user
=====================================================

Required Information
""""""""""""""""""""

  .. code-block:: none

    PI last name, SAF number and bt_uid

  ``xpdAcq`` will load in information automatically unless user delete ``bt_bt.yml`` file in  ``xpdUser/config_base/yml/``.

Goals of the Process
""""""""""""""""""""

  #. Tar entire xpdUser tree with name ``<PIlastname>_<saf#>_<date>_<bt_uid>.tar``
  #. Place a copy of the tarball into remote archive directory ``pe1_data/.userBeamtimeArchive/``
  #. Verify that the archival copy is present and can be accessed
  #. Delete everything except under ``xpdUser``
  #. Keep operator informed of what is going on

Process Steps
"""""""""""""

  #. Please have a rough idea about the file size of ``xpdUser`` tree. Get this information by right click on ``xpdUser`` folder in file browser.
  #. Type ``_end_beamtime()`` at command prompt. Program will start to archive (uncompressed) entire ``xpdUser``. This process usually takes a while. Please be patient and wait until it's finished
  #. After archiving, program will ask you to check remote copy. Please check if file size to remote copy is roughly as large as the size to local ``xpdUser`` tree.
  #. Now there could be two possibility

    * **File size and contents of remote copy are confirmed to be consistent wit local tree**

      Enter ``y`` in the interactive command prompt then program will flush all directories under ``xpdUser``
      and successfully end a beamtime.

    * **File size or contents in remote copy appear to be inconsistent with local tree**

      Please answer ``n`` in the interactive command prompt and program will stop at this point.
      No user data will be removed. Please report a bug on `GitHub <https://github.com/xpdAcq/xpdAcq>`_