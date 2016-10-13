.. _release_note:

Release Notes
--------------

``v0.5``
========

This is a stable release of ``xpdAcq`` software.

New features introduced to this version:

  * flexibility of running customized ``bluesky`` plans while keeping ``xpdAcq`` dark collection logic.

  * ability of importing metadata from a spreadsheet, open the door for data driven studies.

  * data reduction tools:

    * azimuthal integration using ``pyFAI`` as the back-end
    * auto-masking based on statistics on pixel counts

``v0.5`` supports three kinds of built-in scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)

Additional built-in scan types will be added in future releases.

``v0.5`` supports following automated logics :

  * :ref:`automated dark subtraction <auto_dark>`

  * :ref:`automated calibration capture <auto_calib>`

  * :ref:`automated mask per image <auto_mask>`

This version is fully documented and extensively tested.

``v0.3``
========

This is the first full, stable, release, of xpdAcq software.
It offers functionality to acquire data at XPD but with very limited
tools yet to analyze it.
Future releases will focus more on analysis functionalities.
``v0.3`` is still a limited functionality release in that it only supports three kinds of scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)

Additional scan types will be added in future releases.

However, it does support:
 * automated dark subtraction
 * automated calibration capture.

This version is fully documented and extensively tested.
