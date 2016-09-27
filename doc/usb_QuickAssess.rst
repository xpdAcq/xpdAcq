.. _usb_quickassess:

Initial assessment of your data
-----------------------------------------

Saving tiff files
"""""""""""""""""

The most obvious way of accessing your data is to pull them from centralized
server and save them into workstation at ``XPD``. As we have mentioned in
:ref:`qs`, saving tiff can be done in following ways:

.. code-block:: python

  save_last_tiff() # save tiffs from last scan
  save_tiff(db[-1]) # save tiffs from last scan, same as save_last_tiff()
  save_tiff(db[-3:]) # save tiffs from the most recent 3 scans
  save_tiff(db[-1,-5,-7]) # save tiffs from the most recent 1, 5, 7 scans

All the tiff files will be placed under ``xpdUser/tiff_base`` and you can have
all accesses to them. Here index means slicing and ``-`` sign means *last*.
you can slice whatever you want with various combinations. ``db`` stands for
``databroker`` which is another *awesome* software package developed by NSLS-II
software team. For more information, please see
`here <https://nsls-ii.github.io/databroker/>`_

Automated dark subtraction
""""""""""""""""""""""""""

Like we have mentioned at :ref:`auto_dark`, ``xpdAcq``
helps you keep track if appropriate dark frames have been collected, if you
allow it. With ``auto_dark`` set to True, ``xpdAcq`` can automatically subtract
your light frames from corresponding dark frames when you save your tiffs.

This behavior can be turned off by giving additional argument:

.. code-block:: python

  save_last_tiff(dark_subtraction = False)
  save_tiff(db[-1], dark_subtraction = False)
