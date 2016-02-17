


# Sanjit wants to start a new user.  runs a _start_beamtime
icollection
_start_beamtime()
    #Requests IS to move the user yaml files to the xpdUser directory, if directories are clean 
    Billinge
    200384
    0.182
    [('Liu','Timothy',789123),('Terban','Max',2342134),('Ghose','Sanjit',2870)]
# If _end_beamtime() has been run successfully all goes well, otherwise politely told to run _end_beamtime
_end_beamtime()
    # program asks...do you want to proceed?  
    Do we want it to ask some kind of password or something here?
    # program archives all the data, checks they are archived, and empties the directories
# Sanjit loads user yaml files into config_base/yaml

*********************************
#future behavior:. Requires access to a user database
icollection
_start_beamtime
    #after checking for a clean environmnet, program asks for SAFn
    2003568
    #program loads all experimenter info, sample info and user YAMLs from user database
