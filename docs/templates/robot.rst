.. _robot:

Using the Robot
===============

XPD is equipped with a sample loading robot, which requires special syntax to use properly.

0. Load data into ``bt`` as usual
----------------------------------

Follow the normal routine for loading data from the sample spreadsheet.

1. Tell ``bt`` about where the samples are loaded in the robot magazine
-----------------------------------------------------------------------

To use the robot properly ``bt`` needs to know where the samples are loaded.
This is achieved by running ``bt.robot_location_number()``.
This will prompt you to enter the location for each sample currently in
``bt``.
If the sample is not in the magazine that's ok just leave the prompt
 blank and hit ``<enter>``.


2. Run ``xrun`` with the robot flag
-----------------------------------

To run the scans run
``run(<list of sample numbers>, <scan number>, robot=True)``.
``xrun`` will report the contents of the scan so you can review it before
executing.

For example

    .. code-block:: python

       xrun([3, 4, 5], 2, robot=True)


Advanced usage
--------------

The robot and ``xrun`` are more flexible than just running one scan.
Multiple scans can be run per sample.

For example here is a run that runs 3 different plans per sample

    .. code-block:: python

       xrun([3, 3, 4, 4, 5, 5], [2, 5]*3, robot=True)

Note that we multiplied the two scans by three to produce a total of six scans,
two per sample.

The number of scans doesn't need to be a multiple of the number of samples.

    .. code-block:: python

       xrun([3, 4, 5, 5], [2, 2, 2, 5], robot=True)

The only constraint is that if the scans are in a list, that the number of
samples needs to equal the number of scans.
Don't worry about double listing a sample, if a sample is listed multiple times
in a row we won't unload and reload the same sample.
