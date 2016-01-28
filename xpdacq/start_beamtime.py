#!/usr/bin/env python

import sys
import os.path


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

    from xpdacq.config import datapath

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

    from xpdacq.config import datapath
    allowed = set(datapath.allfolders)
    spurious = []
    allowed_f = []
    # collect spurious files or directories within the base folder
    for r, dirs, files in os.walk(datapath.base):
        for d in dirs:
            if os.path.join(r, d) not in allowed:
                spurious.append(d)
        # all files are spurious, except for .yaml and .tar files
        spurious +=  [os.path.join(r, f) for f in files if os.path.splitext(f)[1] not in ('.yaml', '.tar')]
        allowed_f += [os.path.join(r, f) for f in files if os.path.splitext(f)[1] in ('.yaml', '.tar')]
        
    if spurious:
        emsg = 'The working directory {} has unknown files:{}'.format(
                datapath.base, "\n  ".join([''] + spurious))
        print(emsg)
        print('Files other than .tar and .yaml files should not exit \n Please contact beamline scientist')
    if allowed_f:
        tar_f = [ el for el in allowed_f if el.endswith('.tar')]
        print('Delete %s....' % tar_f, sep='\n') 
    
    return allowed_f

def _setup_config():
    ''' setup .yaml file and load it
    '''
    allowed_f = _ensure_empty_datapaths()
    yaml_f = [ f for f in allowed_f if f.endswith('.yaml')]
    
    if len(yaml_f) > 1:
        raise RuntimeError('There is more than one config.yaml already exist in working dir, please contact beamline scientist')
        return

    if not yaml_f :
        raise RuntimeError('There is no config.yaml already exist in working dir')
        return

    confirm = input('This config.yaml file will be used: %s \n Is it the one you wish to use? [y]/n    ' % yaml_f) 
    if confirm not in ('y',''):
        print('Alright, please delete unwanted config.yaml file manuall and put it in ~/xpdUser')
        return
    else:
        #FIXME - loading yaml file
        print('load %s' % yaml_f)

    print('\n Everything is ready to begin.  Please continue with icollection.')

def start_beamtime():
    _make_clean_env()
    _ensure_empty_datapaths()
    _setup_config()
    return


if __name__ == '__main__':
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
