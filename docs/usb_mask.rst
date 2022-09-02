Mask Data Injection
===================

In this section, the ``MaskPreprocessor`` is introduced.

MaskPreprocessor
----------------

Users can put the mask data in the event streams by using the
``MaskPreprocessor``.

It puts the mask data in the ``mask`` event stream when a bluesky run is
opened. The mask data is a two dimensional integer numpy array. It
follows the pyFAI mask convention. The ``0`` are good pixels and the
others are bad pixels.

Use in xrun
-----------

The ``MaskPreprocessor`` is implemented in ``xrun``. Users can use
``mask_files`` keyword to give a list of mask files for a detector. The
mask files will be read and the mask will be combined into one and this
mask will be pushed into the ``mask`` event stream with the name of the
``detector``.

.. code:: ipython3

    xrun(
        0, bp.count([detector]),
        mask_files=[(detector, ["mask1.npy", "mask2.npy", "mask3.npy"])]
    )

The allowed file types of the mask are npy, tiff, edf and txt files.

Users can specify different mask files for different detectors.

.. code:: ipython3

    xrun(
        0, bp.count([detector1, detector2]),
        mask_files=[
            (detector1, ["mask1.npy", "mask2.npy",])
            (detector1, ["mask1.npy", "mask3.npy",])
        ]
    )
