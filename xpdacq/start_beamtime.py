#!/usr/bin/env python

import sys
import os.path


def _make_datapaths():
    '''Make a clean environment for a new user
    
    1. make sure that xpdUser is completely empty except for <tarArchive>.tar and/or
         <name>_<saf#>_config.yml
      a. if no, request the user runs end_beamtime
      b. if yes, delete the tar file (it is archived elsewhere),  and create the 
           working directories
    1. look for a userConfig
    1. ask a series of questions to help set up the environment
    '''
    from xpdacq.config import datapath
    for d in datapath.allfolders:
        if os.path.isdir(d):
            continue
        os.mkdir(d)
    print('Working directories have been created:')
    print(datapath.allfolders, sep='\n')
    return


def _ensure_empty_datapaths():
    '''Raise RuntimeError if datapath.base has any file except those expected.
    '''

    from xpdacq.config import datapath
    allowed = set(datapath.allfolders)
    spurious = []
    # collect spurious files or directories within the base folder
    for r, dirs, files in os.walk(datapath.base):
        for d in dirs:
            if os.path.join(r, d) not in allowed:
                spurious.append(d)
            # all files are spurious
        spurious += [os.path.join(r, f) for f in files]
    if spurious:
        emsg = 'The working directory {} has unknown files:{}'.format(
                datapath.base, "\n  ".join([''] + spurious))
        raise RuntimeError(emsg)
    return

def start_beamtime():
    _make_datapaths()
    _ensure_empty_datapaths()
    print('Everything is ready to begin.  Please continue with icollection.')
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
