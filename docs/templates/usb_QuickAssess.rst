.. _usb_quickassess:

Initial assessment of your data
--------------------------------

Saving tiff files
"""""""""""""""""

The most obvious way of accessing your data is to pull them from centralized
server and save them into your working directory. As we have mentioned in
:ref:`qs`, saving tiff can be done in following ways:

.. code-block:: python

  save_last_tiff() # save tiffs from last scan
  save_tiff(db[-1]) # save tiffs from last scan, same as save_last_tiff()
  save_tiff(db[-3:]) # save tiffs from the most recent 3 scans
  save_tiff(db[-1,-5,-7]) # save tiffs from the most recent 1, 5, 7 scans


With this function, the image will be saved to a ``.tiff`` file under ``xpdUser/tiff_base/<sample_name>``
where ``<sample_name>`` is the metadata you entered during :ref:`setting up your Sample object <usb_experiment>`.

The metadata associated with the image will be saved to a ``.yml`` file which is a
text file which can be opened with a text editor.  Saving behavior can be modified
by changing the default function arguments.  Type ``save_last_tiff?``
to see the allowed values..

Here index means slicing and ``-`` sign means *last* You can slice whatever you
want with various combinations.

.. note::

  if you are new to ``python``, please see `here <https://docs.python.org/3.5/tutorial/introduction.html>`_
  for basic information.

``db`` stands for ``databroker`` which is another
*awesome* software package developed by NSLS-II software team. For more information, please see
`here <https://nsls-ii.github.io/databroker/>`_

Automated dark subtraction
""""""""""""""""""""""""""

Like we have mentioned at :ref:`auto_dark`, ``xpdAcq``
helps you keep track of appropriate dark frames. With ``auto_dark`` set to True,
``xpdAcq`` can automatically subtract your light frames from corresponding dark
frames when you save your tiffs.

This behavior can be turned off by giving additional argument:

.. code-block:: python

  save_last_tiff(dark_sub_bool = False)
  save_tiff(db[-1], dark_sub_bool = False)


Save images and also integrate images to a 1D patterns
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""

**save your images and also integrate to a 1D pattern:**

.. code-block:: python

  integrate_and_save_last()   # the most recent scan

You could use this instead of ``save_last_tiff()`` as part of your acquisition
sequence by typing it in the ``collection`` environment.

Or use these in the ``analysis`` environment to be analyzing data over here as
the data are being collected over there...

.. code-block:: python

  h = db[-2:]                               # the last 2 scans
  integrate_and_save(h, save_image=False)   # saves a copy of the 1D diffraction pattern
  h = db[-2]                                # 2 scan ago
  integrate_and_save(h)                     # saves a copy of the image AND a copy of the 1D diffraction pattern

With these functions, the image (if requested) will be saved to a ``.tiff`` file, the mask
(if there is one) will be saved
to a ``.npy`` file, and the masked-image will be integrated and saved to a ``.chi`` file.
The metadata associated with the image will be saved to a ``.yml`` file which is a
text file and can be opened with a text editor.  Masking and calibration behavior
can be modified by overriding the default function arguments.  Type, for example, ``integrate_and_save_last?``
to see the allowed values.
