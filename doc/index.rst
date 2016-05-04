.. xpdAcq documentation master file, created by
   sphinx-quickstart on Thu Jan 28 11:58:44 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

xpdAcq documentation
====================

Introduction
++++++++++++

``xpdAcq`` is a Python package that helps data collection behavior at XPD beamlime.
It is built on an *awesome* NSLS-II Python package `bluesky <http://nsls-ii.github.io/bluesky/>`_

The goal of ``xpdAcq`` package is to simplify your collection and analysis workflow during beamtime,
so that you can focus more on science aspects. ``xpdAcq`` provides an interface for user who doesn't
have extensive Python coding background. Every syntax started from psychological motivation,
like the most important behind ``prun``:

.. code-block:: none

  run this Sample with this ScanPlan

To find more, please go to :ref:`xpdu`

What's new?
+++++++++++

current version : ``v0.3``
"""""""""""""""""""""""""""

This is the first full, stable, release, of xpdAcq software.
It offers functionality to acquire data at XPD but not to analyze it.
Future releases will focus more on analysis functionalities.
``v0.3`` is still a limited functionality release in that it only supports three kinds of scans:

.. code-block:: none

  single-frame (ct)
  time-series (tseries)
  temperature-series scans (Tramp)

Additional scan types will be added in future releases.

However, it does support :
* automated dark subtraction
* automated calibration capture**.

This version is fully documented and extensively tested


.. toctree::
   :maxdepth: 3
   :hidden:

   quickstart

.. toctree::
   :hidden:
   :maxdepth: 3

   xpdusers

.. toctree::
   :maxdepth: 3
   :hidden:

   troubleshooting

.. toctree::
   :maxdepth: 3
   :hidden:

   beamlinestaff
