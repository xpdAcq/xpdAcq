.. _feature:

``xpdAcq`` features
====================

Automated dark collection
--------------------------

* describe dark criteria

Automated calibration capture
-----------------------------

* describe calibration criteria

.. _calib_manual:

Quick guide of calibration steps with pyFAI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. First you will see an image window like this:

  .. image:: ./img/calib_05.png
    :width: 400px
    :align: center
    :height: 300px

  That is the image we want to perform azimuthal calibration with. Use magnify
  tool at the tool bar to zoom in and **right click** rings. Starting from
  the first, inner ring and to outer rings. Usually a few rings (~5) should be
  enough.

  .. image:: ./img/calib_07.png
    :width: 400px
    :align: center
    :height: 300px

2. After selecting rings, click on the *original* terminal and hit ``<enter>``.
Then you will be requested to supply indices of rings you just selected.
Remember index **starts from 0** as we are using ``python``.
After supplying all indices, you should have a window to show your calibration:

  .. image:: ./img/calib_08.png
    :width: 400px
    :align: center
    :height: 300px

  Program will ask you if you want to modify parameters, in most of case, you
  don't have to. So just hit ``<enter>`` in the terminal and integration will be
  done.

3. Finally 1D integration and 2D regrouping results will pop out:

  .. image:: ./img/calib_09.png
    :width: 400px
    :align: center
    :height: 300px

  You can qualitatively interrogate your calibration by looking if lines in
  2D regrouping are straight or not.

  After this step, a calibration file with name ``pyFAI_calib.yml`` will be
  saved under ``/home/xf28id1/xpdUser/config_base``

Alright, you are done then! With ```automated calibration capture`` feature, ``xpdAcq``
will load calibration parameters from the most recent config file.

metadata imported from spreadsheet
-----------------------------------

* spreadsheet parser rule

Auto-masking
-------------

* auto-masking
