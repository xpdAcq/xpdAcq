import os
import sys
import datetime
from xpdacq.config import datapath

#metadata = _bluesky_metadata_store()

BASE = datapath.base
W_DIR = datapath.tif
D_DIR = datapath.dark
R_DIR = datapath.config
S_DIR = datapath.script

# FIXME: confirm where to put backup dir
B_DIR = os.path.expanduser('~/xpdBackup')

if os.path.isdir(B_DIR):
    pass
else:
    os.makedirs(B_DIR)

def end_beamtime():
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc., and archives them to a
    directory in the remote file-store with filename B_DIR/useriD

    '''
    import shutil
 
    #FIXME - a way to confirm SAF_number in current md_class
    #SAF_num = metadata['SAF_number']
    #userID = SAF_num
    #userIn = input('SAF number to current experiment is %s. Is it correct (y/n)? ' % SAF_num)
    #if userIn not in ('y','yes',''):
        #print('Alright, lets do it again...')
        #return
    
    saf_num = input('Please enter your SAF number to this beamtime: ')
    
    PI_name = input('Please enter PI name to this beamtime: ')
    
    time = datetime.datetime.now()
    year = time.year
    month = time.month
    time_info = '_'.join([str(year), str(month)])

    full_info = '_'.join([time_info.strip(), saf_num.strip(), PI_name.strip()])
    
    backup_trunk = os.path.join(B_DIR, full_info)

    print('Current data in tif_base, dark_base, config_base and script_base will be compressed and moved to %s' % B_DIR)
    
    if os.path.isdir(backup_trunk):
        print('a file with the same PI name, SAF number and year-month already exists')
        print('before proceeding, check that you entered the correct information')
        print('do you want to create a new backup directory for a new beamtime with this user?')
        print('to add files to the existing backup directory hit return.')
        respo = input('Otherwise, enter a new directory name, e.g., "secondbeamtime":')
        if str(respo) != '':
            new_path = os.path.join(B_DIR, full_info + str(respo))
            backup_trunk = new_path
        else:
            print('continue...')
    
    print('Files under %s will be compressed to a .tar file and it will be located at:' % BASE)
    shutil.make_archive(full_info, 'tar', B_DIR, BASE, owner = PI_name.strip(), verbose=1, dry_run=1)
    user_confirm = input('Is it correct? [y]/n ')
    if user_confirm not in ('y', ' '):
        print('Alright, please start again')
        return
    else:
        # FIXME - it doesn't work for a directory....
        shutil.make_archive(full_info, 'tar', B_DIR, BASE, owner = PI_name.strip(), verbose=1, dry_run=0)
        print('Files have been compressed')
        print('Beamline scientist can decide if files under %s are going to be keep')
    
if __name__ == '__main__':
    end_beamtime()
