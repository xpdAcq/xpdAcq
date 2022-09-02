Automatic Dark Frame
====================

In this section, the automatic dark frame in the ``xpdAcq`` is
introduced.

Dark Frame Preprocessor
-----------------------

The dark frame is taken care by ``DarkPreprocessor``.

It is registered in the ``xrun.dark_preprocessors`` list and will be
automatically applied on the users’ plan when the ``xrun`` is called.

.. code:: ipython3

    xrun.dark_preprocessors




.. parsed-literal::

    [<DarkPreprocessor 0 snapshots cached>,
     <DarkPreprocessor 0 snapshots cached>,
     <DarkPreprocessor 0 snapshots cached>]



There could be more than one preprocessor, each for a different detector
or a different strategy for the same detector.

Logic
-----

Here is the introduction of the logic of the automatic dark frame. When
``DarkPreprocessor`` finds a ``trigger`` of the ``detector`` and this
``trigger`` is not for a dark frame (labeled by ``dark_group_prefix``),
it will decide what to do based on the situations. The logic is shown in
the peseudocode below.

::

   if (no dark frames have been taken before):
       take the first dark frame and save it in the cache
   else:
       if (they were not taken under the same situation):
           take a new dark frame and save it in the cache
       else:
           if (they expired):
               take a new dark frame and update the cache
           else:
               don't take new dark frame but use the dark frame in the cache

Here, the ``taken under the same situation`` means that the values of
the ``locked_signals`` are the same. This criterion can be used to take
new dark frame when the frame acquisition time or the number of frames
per image change.

The ``expired`` means that the life time of the cached dark frame is
longer than the ``max_age``.

The ``take a dark frame`` means a series of operations including:

-  close shutter if it is not closed

-  unstage and stage detector to make sure the dark frame is in an
   individual tiff file

-  trigger detector

-  wait for the detector to finish counting

-  unstage and stage detector to make sure the detector save the future
   frames in a separate tiff file

-  move the shutter to the previous state before the dark frame

Tune Configuration
------------------

The configuration of the ``DarkPreprocessors`` can be tuned by directly
changing the attribute of its class. Below is an example to tune the
``max_age`` to ``0.``, which means that a new dark frame will always be
collected whenever a light frame is going to be taken.

.. code:: ipython3

    xrun.dark_preprocessors[0].max_age = 0.

If there is no need to use this preprocessor, below is the way to
disable it.

.. code:: ipython3

    xrun.dark_preprocessors[0].disable()

If it needs to be used after disabled, below is the way to enable it
again.

.. code:: ipython3

    xrun.dark_preprocessors[0].enable()

Usage
-----

Usually, users don’t need to create the these preprocessors. The
preprocessors will be created during the start up of the ipython
session. Users just need to run the ``xrun`` as usual.

.. code:: ipython3

    xrun(0, 1)


.. parsed-literal::

    INFO: requested exposure time = 0.1 - > computed exposure time= 0.1
    INFO: Current filter status
    INFO: flt1 : In
    INFO: flt2 : In
    INFO: flt3 : In
    INFO: flt4 : In
    
    
    Transient Scan ID: 1     Time: 2022-04-13 10:55:26
    Persistent Unique Scan ID: '6c700510-65c9-4025-8d7e-5352cb9fdf8b'
    New stream: 'dark'
    New stream: 'primary'
    +-----------+------------+
    |   seq_num |       time |
    +-----------+------------+
    |         1 | 10:55:27.0 |
    +-----------+------------+
    generator count ['6c700510'] (scan num: 1)




.. parsed-literal::

    ('6c700510-65c9-4025-8d7e-5352cb9fdf8b',)



Dark Frame Data Stream
----------------------

The dark frames are saved in the ``dark`` stream by default while the
light frames are in the ``primary`` stream by default.

.. code:: ipython3

    run = db[-1]
    light_image = next(run.data("detector_image", stream_name="primary"))[0]
    dark_image = next(run.data("detector_image", stream_name="dark"))[0]

.. code:: ipython3

    import numpy as np
    import matplotlib.pyplot as plt
    import xarray as xr
    
    
    def visualize(light_image: np.ndarray, dark_image: np.ndarray) -> None:
        subtracted_image = light_image - dark_image
        images = [light_image, dark_image, subtracted_image]
        titles = ["Light", "Dark", "Subtracted"]
        _, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=72.)
        for image, title, ax in zip(images, titles, axes):
            ax.imshow(image, vmax=7000.)
            ax.set_title(title)
            ax.set_xticks([])
            ax.set_yticks([])
        return

.. code:: ipython3

    visualize(light_image, dark_image)



.. image:: img/dark_frame_logic_24_0.png


Current Limitation
------------------

Current version of the ``DarkPreprocessor`` has the unexpected behavior
if two detectors are triggered simutaneously and two dark frames are
needed at the same time. This was address in `the issue
here <https://github.com/bluesky/bluesky-darkframes/issues/35>`__.

The suggestion is to use ``trigger_and_read`` on the two detector
separately. In the future, the ``DarkPreprocessor`` will be enhanced to
take care of multiple detectors in a coherent way.

More Information
----------------

``DarkPreprocessor`` is a wrapper class of the ``DarkFramePreprocessor``
in the ``bluesky-darkframes`` package. To know more information about
it, please visit the `bluesky-darkframes
documentation <https://blueskyproject.io/bluesky-darkframes/>`__.
