.. xpdAcq documentation master file, created by
   sphinx-quickstart on Thu Jan 28 11:58:44 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

xpdAcq documentation
====================

Introduction
++++++++++++

To post questions about anything XPD, including software, and to see archived answers, please join the `XPD-Users Google group
<https://groups.google.com/forum/#!forum/xpd-users;context-place=overview>`_

``xpdAcq`` is a Python package that aids data collection at the XPD beamlime. It is built on top of and augments the NSLS-II data acquisition Python
package `bluesky <http://nsls-ii.github.io/bluesky/>`_ .

XPD may be operated directly by bluesky, or using xpdAcq.

The goal of the ``xpdAcq`` package is to simplify your collection and analysis workflow during beamtime,
so that you can focus more on scientific aspects of your experiment. Additionally, ``xpdAcq`` provides an interface
that needs less Python experience than the current native bluesky interface.

We hope that you find it intuitive, like the most important function to run a scan, ``xrun``:

.. code-block:: python

  xrun(sample-info, scan-info) #run this Sample with this Scan-Plan

To get started, please go to :ref:`quick_start`

If you have suggestions for new features in xpdAcq, or want to report a bug or simply ask a question about
the software, please post it as a new thread at `XPD-Users
<https://groups.google.com/forum/#!forum/xpd-users;context-place=overview>`_

What's new?
+++++++++++

current version : ``v0.6.0``
""""""""""""""""""""""""""""

This is a stable release of ``xpdAcq`` software.

This version is fully documented and extensively tested.

New features introduced to this version:

* Integration with automated data reduction pipeline. Now live visualization and
  automated data-saving is supported. For the details about the pipeline, please
  refere to `xpdAn documentation <http://xpdacq.github.io/xpdAn/>`_.

* Advanced shutter control logic for temepratrue-rampling scan plan,
  ``Tlis`` and ``Tramp``. Shutter will remain closed in between
  exposures, which prevent detector from burnning. This behavior can
  be overridden, leaving the fast shutter open for the entire scan.
  Please refer to our docstring for details.

* Refined metadata logic. We implement ``client-server`` logic which
  would largely enhance the linking between associated scans. For
  more details, please refer to :ref:`client_server_md`.

* Current version supports following built-in scans:

  .. code-block:: none

    single-frame (ct)
    time-series (tseries)
    temperature-series scans (Tramp)
    temperature-list scans (Tlist)


  Additional built-in scan types will be added in future releases.


.. toctree::
   :maxdepth: 3
   :hidden:

   quickstart

.. toctree::
   :maxdepth: 3
   :hidden:

   xpdusers

.. toctree::
   :maxdepth: 3
   :hidden:

   beamlinestaff

.. toctree::
   :hidden:
   :maxdepth: 3

   troubleshooting

.. toctree::
   :maxdepth: 3
   :hidden:

   release_note
