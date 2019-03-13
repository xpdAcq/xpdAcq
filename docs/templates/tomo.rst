.. _tomo:

Running Tomography
==================

The XPD acquisition and analysis stack supports the acquisition and processing
of tomographic data in both full field and pencil beam geometries.

XPD is equipped with a sample loading robot, which requires special syntax to use properly.

Running a tomographic scan
--------------------------

There are three scans currently supported. Each scan is delineated by
different metadata added at the beginning of the scan:

1. Full Field

.. code-block:: python

     {'tomo': {'type': 'full_field',
               'rotation': 'motor1',
               'center': 123.3}}

2. 2D Pencil Beam

.. code-block:: python

     {'tomo': {'type': 'pencil',
               'rotation': 'motor1',
               "translation": "motor2",
               'center': 123.3}}

3. 3D Pencil Beam

.. code-block:: python

     {'tomo': {'type': 'pencil',
               'rotation': 'motor1',
               "translation": "motor2",
               "stack": "motor3"
               'center': 123.3}}

You will need to fill in the ``center`` field with the correct rotation axis location (found via a line scan of the sample).
You will also need to fill in the various motor names associated with the sample rotation, translation, and stack translation (z direction).

Here is an example call to ``xrun`` running a tomographic scan

.. code-block:: python

    xrun(3, bp.grid_scan([pe1c],
         z_motor, 0, 2, 10,  # This is the out of plane translation
         theta_motor, 0, 180, 181, True,  # The theta rotation
         x_motor, 200, 401, 200, True,  # The translation
            md={
                "tomo": {
                    "type": "pencil",
                    "rotation": "theta_motor",
                    "translation": "x_motor",
                    "stack": "z_motor",
                    # we subtract 200 because we are starting at 200
                    # (and the center is measured in pixels)
                    "center": 300 - 200,
                }
            },
        )
    )

Once this scan starts the automated data processing software will kick in to create reconstructions of the data for each quantity of interest.
