.. _troubleshooting:

Quick quesitons
===============

Q: **Why does my scan halt for no reason? I followed your guide and no error message popped.**

    That is most likely come from confusion at machine level.
    Don't worry, just make sure **there is only one XPD control running on this computer.**.
    ``XPD control`` can be launched from the shortcut in desktop:

    .. image:: /xpd_control.png
     :width: 60px
     :align: center
     :height: 80px

    After launched it, a window similar to this should pop out:

    .. image:: /pe1c_ioc.png
     :width: 400px
     :align: center
     :height: 300px

    Each ``XPD control`` window means a control panel between XPD computer and experiment apparatuses, such as area detector or motor.
    Therefore we should avoid having multiple ``XPD control`` running at the same time.
    To make sure there is only one ``XPD control`` running, move to top right corner and click ``Activities``.
    Then you should see all currently active windows. Close duplicated control panels (if any) then it should work.

    If scan still halts, please contact beamline scientist immediately for bug report.

More
--------------
 #. :ref:`usb_where`
 #. :ref:`usb_gotchas`
