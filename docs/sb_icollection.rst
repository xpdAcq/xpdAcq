.. _sb_icollection:


Overview of the bsui+xpdAcq environment
----------------------------------------------

All data collection at NSLS-II is carried out through a powerful
Python-software-language based interface which runs in an ipython interactive
session. By typing ``bsui`` at the unix prompt (command line) in a terminal
window at the XPD computer you begin an ipython session and preload an ipython
profile (called ``collection``) that contains all the software to run the NSLS-II
data collection software.

You can tell when you are in the ``collection`` environment
because you will see ``(collection-yyQn.x)`` at the beginning of the command-line.
``yy`` stands for year and ``Qn.x`` tells detailed information about the
version. For example, ``collection-17Q1.0`` would mean the fist version of
quarter 1, in 2017.When you are not in the environment you won't see that. There is also an analysis environment, which is currently called ``analysis``,
that is very similar to the ``collection`` environment but it is for data
analysis functions and you cannot control any XPD hardware from it.  This may
be run on a different computer than the control software, as long as it can see
the NSLS-II data database.   This environment is activated by typing ``ianalysis``
in a fresh terminal on one of the XPD linux computers.

Inside the ``collection-yyQn.x`` environment you can type commands that will control the
diffractometer, collect data, and also extract data from the NSLS-II database.
The NSLS-II data acquisition environment is powerful and flexible, but there is a
stiff learning curve to using it.  We have therefore added a layer on top that
is a package of programs called ``xpdAcq`` that are designed to make the data
acquisition at XPD easier and more robust for most people.  We strongly suggest
that you use the xpdacq functions as much as possible.

NSLS-II data philosophy
+++++++++++++++++++++++

NSLS-II is committed to archiving all raw data, and making it available to
authorized users.  For this to succeed it is important to be able to find the
data when it is desired.  The basic philosophy at NSLS-II is therefore to
tag every dataset with unique-ID tags, and to save rich metadata with each saved
frame that can be searched on to find the data.  The ``xpdAcq`` package is designed
to make the user inputs easier when collecting data, and to facilitate the saving
of rich and correct metadata with the saved data for easier retrieval later.  It is
hoped that this will greatly speed up and facilitate users' later data analysis
and modeling workflows.
You are reading the xpdAcq documentation.  Documentation for the NSLS-II data acquisition
package, 'Bluesky' can be found `here <http://nsls-ii.github.io/bluesky/>`_.

xpdAcq philosophy
+++++++++++++++++

When we are running the experiment we pretty much just want to be worrying about
setting up and running the scans, but to find the data later, and to help with
processing it (in the future the metadata will be passed directly to the data
reduction software) it is important that a complete stack of metadata is saved
with each scan.  The philosophy of the xpdAcq software is to accomplish this.

Metadata comes from a number of sources: beamtime information, sample information, scan information, and
information coming from hardware during the experiment (such as sample temperature, for example).
With this in mind, ``xpdAcq`` assumes that you may be doing multiple scans on the same sample,
and so we define a scan as the union of a scan-plan (which contains all the parameters of the
scan you want to run) and a sample.  Beamtime metadata consists of the SAF number, PI name,
list of experimenters and so on and is set up by the beamline scientist at the beginning of your
beamtime.  There can be a wealth of information about your sample that you want to save.  To make 
this easier, we provide an excel spreadsheet that you can fill in before (or during) your experiment
that contains information about each separate sample that you will run.
When you run a scan using ``xrun`` and specifying a scan-plan and a sample, 
``xpdAcq`` will take all the beamtime metadata, the sample metadata, and all the parameters of the scan,
and save it in the scan header in the metadata store, linked to the actual dataset itself. You may also
specify more metadata to save when the scan is run by specifying it in ``xrun``.   Additional metadata
are also saved, such as a link to the ``xpdAcq``'s best guess at the right dark-collection to use for correcting
your scan data, calibration parameters for the experimental setup, and so on.  These can be overridden during analysis
so don't worry if they are incorrectly saved, but following the preferred ``xpdAcq`` workflow during data collection
can save you a lot of  time later by making these guesses correct.   Hardware generated metadata, such as sample temperature,
are also saved and can be retrieved later.

Later you will be able to use the scan metadata to search for your scans from the XPD database.  For example, a search
on the PI-last name and a date-range will return all the datasets you collected in that date-range.  If you add sample name
it will return all the scans done on that sample in that date-range and so on.

With this information in mind, please go ahead and start the step-by-step process
of setting up your beamtime in :ref:`usb_Beamtime`


return to :ref:`xpdu`
