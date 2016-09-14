# Sanjit wants to start a new user.  runs a _start_beamtime
icollection
_start_beamtime()
# Program checks for clean xpdUser tree and exits if not clean
# Not implemented##
# Program requests Sanjit to move a tar file containing the user yaml files to the xpdUser directory, then hit return to continue
# Not implemented##
Testing
200384
0.182
[('Liu', 'Timothy', 789123), ('Terban', 'Max', 2342134)
    , ('Ghose', 'Sanjit', 2870)]  # Program builds directories
# If there is a yaml file tarball, unpack it to config_base/yaml
# Create the bt data object
bt.list()
# Return bt.md for checking
bt.md
# Exit **** ** ** ** ** ** ** ** ** ** ** ** ** ** ***
# future behavior:. Requires access to a user database
icollection
_start_beamtime  # after checking for a clean environmnet, program asks for SAFn
2003568
# program loads all experimenter info, sample info and user YAMLs from user database

** ** ** ** ** ** ** ** ** ** ** ** ** ** **
# Sanjit wants to archive, export and finish an old beamtime.
_end_beamtime()
Do
we
want
it
to
ask
some
kind
of
password or something
here?
# program deletes export tar file(s) from Export directory
# program makes tarball of entire xpdUser tree into tarball and puts it in archival place
# program checks that it is there and that it is about the right size
# program compresses it.
# program asks...file has been backed up <here>. everything will be deleted, do you want to proceed?
# on y or Y, program cd's to directory above xpdUser
# program wipes everything
# program replaces xpdUser directory
# program places copy of compressed file into xpdUser
# program lets Sanjit and/or User know  where the export files are and safe to exit.
