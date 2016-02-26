#UC1
# 1. user is ready to set up her acquire objects
# 2. user checks the current bt.list and sees just bt Beamtime object
# 3. user creates an experiment object by typing new_exp() 
  simon working on this
# 4. program asks the exp name
# 5. program removes internal and external white-spaces and checks if the experiment exists
#   5.1 if name exists program exits with message "experiment with name %s exists.  If you are trying to update it please use 'edit_exp'"
#   5.2 if it doesn't exist:
      # create exp uid
      # show user the existing metada that will be included from the bt object. Say "to change existing metadata for all experiments run edit_bt. To extend metadata just for current experiment ..." (have to think of a good way of doing this)
      # ask user for exp metadata and set it.
 # write yaml file. Save bt metadata not directly in the file, but save the bt_name and use this to read the upstream metadata in load_yaml
 # update yaml_list.yml file that contains the list of yml objects.  This will be returned when bt.list is called, rather than one obtained dynamically. This ensures that objects don't change position in the list.
 # functional requirements: separate input and functional logic
 #                          wrap input statements to make them testable
 #                          try and make easily extendable when adding new required metadata fields
****************
# UC2
# as UC1 but user wants to edit an existing experiment
   # if doesn't exist, exit telling to run new_exp()
   # as above, but 
       # set uid to the same value as it was in the original exp
       # give existing values as defaults when the questions are asked
*****************
# UC3
# as UC1 and UC2 but for smaple info
*****************
# UC4
# user reequests a list of existing objects.  List returns obj type, obj name and position in list.  List position is immutable
# first few are standard:  (note, this is the behavior for spec-like workflow, for l-type users....without any setup lusers can type prun(bt.get(1),bt.get(6)))
    # list[0] is bt
    # list[1] is ex dummy (contains dummy information)
    # list[2] is sa dummy (contains dummy info)
    # list[3] is sc 'ct#s' (where # is the detector frame-time), e.g., 'ct0.1s'
    # list[4] is sc ct2#s   0.2
    # list[5] is sc ct4#s   0.4
    # list[6] is sc ct1.s   
    # list[7] is sc ct10.s  
    # list[8] is sc ct30.s 
    # list[9] is sc ct1.m   1.m and 60.s are equivalent.  Ideally save one scan object for this but allow user to call it either way. 
    # list[10] is sc ct10.m 
 *********************************
# UC5
#  user wants to remove an object from the list. Types hide_item()
# on future bt.list() requests, this item is not returned, though it remains in the yaml dir and in the list itself, it is just not shown.
# one idea for implementation on this is that list.yaml contains a list of tuples [(type,name,hidebool),()] and so on. 
**********************************
# UC6
# user wants to unhide a list item
# user types unhide_item()
# program lists hidden item
# user selects list of hidden items to unhide
**********************************
# UC7
# user wants to run scans, darks, etc.. 
# user types prun(bt.get(#),bt.get(##)) for sample and scan objects, where # and #$# are the position of the list
**********************************
#UC8
# as UC7 but user is lazy and only wants to type prun(#,##) where # and ## are integers
**********************************
# UC9
# as UC7 user has a good memory for names, so user would rather type prun('samplename','scanname'), e.g., prun('dummy','ct1.0')
**********************************
# UC10
# as UC10 but user can type any combination of objects, ints or strings
***********************************
# Functional requirement:
# remove the delete object functionality.  We never will delete objects now, just hide them.
**********************************
#UC11
# user wants to do a run prun('mysample','ct75.5') but 75.5 doesn't exist
# program says 'scan ct75.5s doesnt exist, do you want to create it now [y],n?
# on '',y' or 'Y' create that scan then run it.
**********************************
# UC12
# as UC11, but the scan exists, the sample doesn't.
# program exits with a kind message to please create that sample object and retry
**********************************
# UC13
# this should have been higher up, but make new_scan(type,name='') function that helps the user to create scan objects
# allowed types are currently ct, tserires, Tramp
# if name is recognizable, create the scan object immediately
# if the name is ambiguous, ask questions