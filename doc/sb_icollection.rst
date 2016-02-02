.. _sb_icollection:


Overview of the icollection+xpdacq environment
----------------------------------------------

All data collection at NSLS-II is carried out through a powerful 
Python-software-language based interface which runs in an ipython interactive
session. By typing ``icollection`` at the unix prompt (command line) in a terminal
window at the XPD computer you begin an ipython session and preload an ipython
profile (called ``collection``) that contains all the software to run the NSLS-II 
data collection software.  You can tell when you are in the ``collection`` environment
because you will see ``[collection]`` at the beginning of the command-line.  When
you are not in the environment you won't see that.

Inside this ``collection`` environment you can type commands that will control the
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
hoped that this will greatly speed up and facilitate users' later workflows.
You are reading the xpdAcq documentation.  Documentation for the NSLS-II data acquisition
package, 'Bluesky' can be found `here <http://nsls-ii.github.io/bluesky/>`_.

xpdAcq philosophy
+++++++++++++++++

Our goal is to maximize the quantity and quality of your metadata whilst minimizing
your typing.  To do this we separate the experimental workflow into a hierarchy
of activities and we associate metadata with each level of the hierarchy.  Each
level of the hierarchy will inherit the metadata in the higher levels of the
hierarchy for saving with the data.

The hierarch is as follows:
 * Beamtime
 
    * Experiment
    
       * Sample
       
          * Scan
          
             * Exposure
     
where it is assumed that a `Beamtime` may consist of one or more `experiments`
(such as "temperature and doping dependence of In1-xGaxA"). Each experiment
will make measurements on one or more `samples` (in the example case the samples
may be GaAs, In0.25Ga0.75As, In0.5Ga0.5As, In 0.75Ga0.25As and InAs) and on each
sample we do one or more `scans` (for example a temperature scan from 100 K to 300 K)
which consist of one or more `exposures`.

When we are running the experiment we pretty much just want to be worrying about
setting up and running the scans, but to find the data later, and to help with
processing it (in the future the metadata will be passed directly to the data
reduction software) it is important that a complete stack of metadata is saved
with each scan.  The philosophy of the xpdAcq software is to accomplish this.

The way this is done is that we associate metadata with each level of the hierarchy
and levels that are lower in the hierarchy inherit the data from the higher levels.
Two required pieces of data at the Beamtime level are ``PIlastName`` and ``SAF#``,
the last name of the PI in charge of the beamtime and the number of the safety 
approval form for the experiment.  This information will be typed once, but saved
with every dataset during that beamtime.  You can create multiple `instances` 
of each metadata level and these will be saved for later use.  So at the 
beginning of the beamtime (or at home before you arrive using the xpdSim package)
you can create a ``myGaAs`` object, an ``myIn25Ga75As``, and so on.  When you create
a scan you just have tell it that the sample is ``myGaAs`` and all the metadata
in myGaAs will automatically be saved with every exposure in that scan.  In ``xpdAcq``
there are helpful functions for setting up these metadata libraries.  In the
future, a GUI is planned to facilitate this even further.

With this information in mind, please go ahead and start the step-by-step process
of setting up your beamtime in :ref:`usb_Beamtime`
  

return to :ref:`xpdu`
