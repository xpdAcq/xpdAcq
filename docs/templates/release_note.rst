.. _release_note:

Release Notes
--------------


``v0.5.2``
==========

This is a stable release of ``xpdAcq`` software.

Addition to all the features of ``v0.5.0``, new features introduced to this version are:

  * functionality to reload beamtime configuration when reenter into ``ipython`` session

  * improved logic of importing metadata from a spreadsheet, information is parsed in a 
    way that facilitates data driven studies.

  * new ScanPlan: temperature list scan ``Tlist``. User can collect data at desired
    temperature points.

``v0.5.2`` supports following built-in scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)
  temperature-list scans (Tlist)

Additional built-in scan types will be added in future releases.

``v0.5.2`` also supports following automated logics :

  * :ref:`automated dark subtraction <auto_dark>`

  * :ref:`automated calibration capture <auto_calib>`

  * :ref:`automated mask per image <auto_mask>`

This version is fully documented and extensively tested.


``v0.5.0``
==========

This is a stable release of ``xpdAcq`` software.

New features introduced to this version:

  * flexibility of running customized ``bluesky`` plans while keeping ``xpdAcq`` dark collection logic.

  * ability of importing metadata from a spreadsheet, open the door for data driven studies.

  * data reduction tools:

    * azimuthal integration using ``pyFAI`` as the back-end
    * auto-masking based on statistics on pixel counts

``v0.5.0`` supports three kinds of built-in scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)

Additional built-in scan types will be added in future releases.

``v0.5.0`` supports following automated logics :

  * :ref:`automated dark subtraction <auto_dark>`

  * :ref:`automated calibration capture <auto_calib>`

  * :ref:`automated mask per image <auto_mask>`

This version is fully documented and extensively tested.

``v0.3.0``
==========

This is the first full, stable, release, of xpdAcq software.
It offers functionality to acquire data at XPD but with very limited
tools yet to analyze it.
Future releases will focus more on analysis functionalities.
``v0.3.0`` is still a limited functionality release in that it only supports three kinds of scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)

Additional scan types will be added in future releases.

However, it does support:
 * automated dark subtraction
 * automated calibration capture.

This version is fully documented and extensively tested.
