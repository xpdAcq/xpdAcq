#!/usr/bin/env python

import sys
import os.path
import os
import sys
import datetime
from xpdacq.config import datapath


def _make_clean_env():
    '''Make a clean environment for a new user
    
    1. make sure that that the user is currently in /xpdUser  if not move to ~/xpdUser and try again
    2. make sure that xpdUser is completely empty or contains just <tarArchive>.tar and/or
         <PIname>_<saf#>_config.yml
      a. if no, request the user runs end_beamtime and exit
      b. if yes, delete the tar file (it is archived elsewhere),  and create the 
           working directories. Do not delete the yml file.
    1. look for a <PIname>_<saf#>_config.yml and load it.  Ask the user if this is
    the right one before loading it.  If yes, load, if no exit telling user to manually
    delete the yml file and install the correct one in dUser directory, if it exists.
    1. ask a series of questions to help set up the environment. Save them in the
    <PIname>_<saf#>_config.yml file.  Create this if it does not already exist.
    '''
    ### create dirs and move to ~/xpdUser

    for d in datapath.allfolders:
        if os.path.isdir(d):
            continue
        os.mkdir(d)
    print('Working directories have been created:')
    print(datapath.allfolders, sep='\n')
    os.chdir(datapath.base)

    return


def _ensure_empty_datapaths():
    '''Raise RuntimeError if datapath.base has any file except those expected.
    '''
    allowed = set(datapath.allfolders)
    spurious = []
    allowed_f = []
    # collect spurious files or directories within the base folder
    for r, dirs, files in os.walk(datapath.base):
        for d in dirs:
            if os.path.join(r, d) not in allowed:
                spurious.append(d)
        # all files are spurious, except for .yml and .tar files
        spurious +=  [os.path.join(r, f) for f in files if os.path.splitext(f)[1] not in ('.yml', '.tar')]
        allowed_f += [os.path.join(r, f) for f in files if os.path.splitext(f)[1] in ('.yml', '.tar')]
        
    if spurious:
        emsg = 'The working directory {} has unknown files:{}'.format(
                datapath.base, "\n  ".join([''] + spurious))
        print(emsg)
        print('Files other than .tar and .yml files should not exit \n Please contact beamline scientist')
    if allowed_f:
        tar_f = [ el for el in allowed_f if el.endswith('.tar')]
        print('Delete %s....' % tar_f, sep='\n') 
    
    return allowed_f

def _setup_config():
    ''' setup .yml file and load it
    '''
    allowed_f = _ensure_empty_datapaths()
    yml_f = [ f for f in allowed_f if f.endswith('.yml')]
    
    if len(yml_f) > 1:
        raise RuntimeError('There is more than one config.yml already exist in working dir, please contact beamline scientist')
        return

    if not yml_f :
        raise RuntimeError('There is no config.yml already exist in working dir')
        return

    confirm = input('This config.yml file will be used: %s \n Is it the one you wish to use? [y]/n    ' % yml_f) 
    if confirm not in ('y',''):
        print('Alright, please delete unwanted config.yml file manuall and put it in ~/xpdUser')
        return
    else:
        #FIXME - loading yml file
        print('load %s' % yml_f)

    print('\n Everything is ready to begin.  Please continue with icollection.')

def start_beamtime():
    _make_clean_env()
    _ensure_empty_datapaths()
    _setup_config()
    return
    

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
    
    os.chdir(B_DIR)
    print('Files under %s will be compressed to a .tar file and it will be located at:' % BASE)
    tar_return = shutil.make_archive(full_info, 'tar', BASE, owner = PI_name.strip(), verbose=1, dry_run=1)
    print(tar_return)
    user_confirm = input('Is it correct? [y]/n ')
    if user_confirm not in ('y', ' '):
        print('Alright, please start again')
        os.chdir(BASE)
        return
    else:
        # FIXME - it doesn't work for a directory....
        shutil.make_archive(full_info, 'tar', base_dir = BASE, owner = PI_name.strip())
        print('Files have been compressed')
        print('Beamline scientist can decide if files under %s are going to be kept' % BASE)
        os.chdir(BASE)
    
if __name__ == '__main__':
    end_beamtime()
    try:
        start_beamtime()
    except RuntimeError as e:
        print(e, file=sys.stderr)
        print("Ask beamline scientist what to do next.", file=sys.stderr)
        sys.exit(1)



'''
## function deals with metadata should be moved to xpd_md_class.py
def _input_metadata():
    #Ask user for various metadata related to this experiment.

    from bluesky.standard_config import gs
    saf = input('SAF number of this beamtime: ')
    gs.RE.md['SAF_number'] = saf.strip()
    ipn = input('Principal Investigator (PI) name: ')
    gs.RE.md['pi_name'] = pn.strip()
    enames = input('Other experimenter names separated by commas: ')
    exlist = [n.strip() for n in enames.split(',')]
    exlist = [pn] + [n for n in exlist if n != pn]
    gs.RE.md['experimenters'] = exlist
    # TODO - check if user wants to reset the scan_id
    current_scan_id = gs.RE.md['scan_id']
    reset_scanid = input('Current scan_id is %s. Do you wish to reset scan_id? (y/N) ' % current_scan_id)
    if reset_scanid == 'y':
        print('Reset scan_id to 1')
        gs.RE.md['scan_id']= 1
    else:
        print('Keep current scan_id')

    return
'''
