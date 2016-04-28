.. _troubleshooting:

Troubleshooting
---------------

Why does my scan halt for no reason?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Sometimes you might find your scans halt for no reason, not even an error message.
That is most likely come from confusion at machine level.
Don't worry, just make sure **there is only one XPD control running on this computer.**.
``XPD control`` can be launched by double-click on shortcut in desktop:

  .. image:: ./xpd_control.png
    :width: 60px
    :align: center
    :height: 80px

After launched it, a window similar to this should pop out:

  .. image:: ./pe1c_ioc.png
    :width: 400px
    :align: center
    :height: 300px

Each ``XPD control`` window means a control panel between XPD computer and experiment apparatuses, such as area detector or motor.
Therefore we should avoid having multiple ``XPD control`` running at the same time.
To make sure there is only one ``XPD control`` running, move to top right corner and click ``Activities``.
Then you should see all currently active windows. Close duplicated control panels (if any) then it should work.

If scan still halts, please contact beamline scientist immediately for bug report.


Where did all my Sample and Scan objects go?????
++++++++++++++++++++++++++++++++++++++++++++++++

You just spent hours typing in metadata and creating
:ref:`sample <usb_experiment>` and :ref:`scan <usb_scan>`
objects, and now they have suddenly disappeared!  This
is a disaster!

As Douglas Adams taught us `DON'T PANIC` .  This is actually
`normal` (or at least `expected` ) behavior in xpdAcq.  Remember that
one of the design goals of the software project was to minimize
users' typing.  The design had to take into account that the
collection ipython environment is not so stable
(e.g., see :ref:`troubleshooting` ) and we should expect periodic
restarts of it.  How bad if we had to retype our metadata every
time?  So every time you create an xpdAcq acquisition object,
the details are saved to a file on the local hard-drive.  When
``icollection`` is run, the main ``bt`` object (if it exists) is
automatically reloaded, but not the other acquisition objects.
But don't worry, they are all safe and sound.
