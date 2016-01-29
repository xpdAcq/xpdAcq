.. _sb_overview:

Overview of xpd acquisition environment
---------------------------------------

All experiments will be carried out in the ``~/xpdUsers`` directory tree.

At the beginning of the beamtime we will present to users a set of empty directories
inside  ``~/xpdUsers``.  These will be

+---------------+------------------------------------------------------------+
|directory name |contents                                                    |
+===============+============================================================+
|Import         |User places their pre-made beamtime metata in a file called |
|               |``<PIname>_<saf#>_config.yml``                              |
+---------------+------------------------------------------------------------+
|Export         |A zipped tar file will be placed here at the end of the     |
|               |beamtime containing *everything* that the user created in   |
|               |in any directory below ``~/xpdUser``. This is for the user  |
|               |to take home on their hard-drive                            |
+---------------+------------------------------------------------------------+
|config_base    |This contains the config file used by ``xPDFsuite``.        |
|               |xPDFsuite will write this file.  The user should not edit or|
|               |add anything to this directory                              |
+---------------+------------------------------------------------------------+
|tif_base       |This is where all the image files (.tiff) are stored *that* |
|               |*the user extracts* from the database using the dataBroker  |
|               |scripts during the experiment.                              |
+---------------+------------------------------------------------------------+
|dark_base      |This is where image files from dark-exposures are stored    |
+---------------+------------------------------------------------------------+
|userScripts    |This is a handy space where the users can write their own   |
|               |experiment scripts and save them. They will be bundled up   |
|               |at the end of the experiment for shipping home              |
+---------------+------------------------------------------------------------+
|userAnalysis   |Users can create any sets of directories under here for     |
|               |storing analyzed files (for example, saved by xPDFsuite).   |
|               |it is expected that most of these will be 1D files such as  |
|               |raw 1D diffraction intensities, g(r) and F(Q) files.        |
+---------------+------------------------------------------------------------+
|...            |Actually, the users can create any directories and files    |
|               |they want and they will be bundled, tarred and zipped at the|
|               |end for them to take home.                                  |
+---------------+------------------------------------------------------------+

return to :ref:`bls`
