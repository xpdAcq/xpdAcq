#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import sys
import os
import datetime
import shutil
from xpdacq.config import DataPath

from time import strftime

B_DIR = os.getcwd()


def _make_clean_env(datapath):
    '''Make a clean environment for a new user

    1. make sure that that the user is currently in /xpdUser
       if not move to ~/xpdUser and try again

    2. make sure that xpdUser is completely empty or contains just
       <tarArchive>.tar and/or <PIname>_<saf#>_config.yml
      a. if no, request the user runs end_beamtime and exit
      b. if yes, delete the tar file (it is archived elsewhere),
         and create the working directories. Do not delete the yml file.

    3. look for a <PIname>_<saf#>_config.yml and load it.  Ask the user if
       this is the right one before loading it.  If yes, load, if no exit
       telling user to manually delete the yml file stall the correct one in
       dUser directory, if it exists.

    4. ask a series of questions to help set up the environment. Save them
       in the <PIname>_<saf#>_config.yml file.  Create this if it does not
       already exist.

    Parameters
    ----------
    datapath : ??
        Base directory to work in
    '''

    for d in datapath.allfolders:
        os.makedirs(d, exist_ok=True)
    print('Working directories have been created:')
    print(datapath.allfolders, sep='\n')
    os.chdir(datapath.base)
    print('')
    return


def _ensure_empty_datapaths(datapath):
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
        spurious.extend([os.path.join(r, f) for f in files
                         if os.path.splitext(f)[1] not in ('.yml', '.tar')])
        allowed_f.extend([os.path.join(r, f) for f in files
                          if os.path.splitext(f)[1] in ('.yml', '.tar')])

    if spurious:
        emsg = 'The working directory {} has unknown files:{}'.format(
                datapath.base, "\n  ".join([''] + spurious))
        print(emsg)
        print('Files other than .tar and .yml files should not exit \n'
              'Please contact beamline scientist')
    if allowed_f:
        tar_f = [el for el in allowed_f if el.endswith('.tar')]
        print('Delete %s....' % tar_f, sep='\n')
        for f in tar_f:
            os.unlink(f)

    return allowed_f


def _setup_config(datapath):
    ''' setup .yml file and load it
    '''
    allowed_f = _ensure_empty_datapaths(datapath)
    yml_f = [f for f in allowed_f if f.endswith('.yml')]

    if len(yml_f) > 1:
        print('There is more than one config.yml already exist in working dir,'
              ' Please contact beamline scientist\n')
        return

    if not yml_f:
        print('WARNING: There is no config.yml in working dir')
        print('If you have one, please add it to ')
        print('(That is fine if you are doing simulation)\n')
        return

    confirm = input('This config.yml file will be used: %s \n'
                    'Is it the one you wish to use? [y]/n    ' % yml_f)

    if confirm not in ('y', ''):
        print('Alright, please delete unwanted config.yml file manuall '
              'and put it in ~/xpdUser\n')
        return
    else:
        # FIXME - loading yml file
        print('load %s' % yml_f)

    print('\n Everything is ready to begin.  '
          'Please continue with icollection.\n')


def _get_time(date=True):
    ''' function to grab current time info

    Parameters:
    -----------

    date
        bool - if yes, grab full time info. else only grab upto month

    Retunrs
    -------
    time_info
        str - time info

    '''

    time = datetime.datetime.now()
    year = time.year
    month = time.month
    day = time.day

    if date:
        time_info = '_'.join([str(year), str(month), str(day)])
    time_info = '_'.join([str(year), str(month)])

    return time_info


def _flush_dir(folder_path):
    ''' delete files and subdir under folder

    BEWARE!
    '''

    import os, shutil
    e = 'No files inside this directory, pass'
    if os.listdir(folder_path):
        for f in os.listdir(folder_path):
            file_path = os.path.join(folder_path, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except:
                print(e)
    else:
        pass

    # if not os.listdir(folder_path):
    #    print('flushed directroy %s' % folder_path)


def _tar_n_move(f_name, src_dir, dest_dir, dry_run=False):
    ''' compree a source directory and output to a dest_dir
    '''
    import os
    import shutil

    cwd = os.getcwd()  # current working directory
    os.chdir(dest_dir)
    print('Files under %s will be compressed to a .tar file and '
          'it will be located at:' % src_dir)
    tar_return = shutil.make_archive(f_name, 'tar', base_dir=dest_dir,
                                     verbose=True, dry_run=True)
    print(tar_return)
    user_confirm = input('Is it correct? [y]/n ')
    if user_confirm not in ('y', ''):
        os.chdir(cwd)
        raise RuntimeError('YOU ARE FINE :)))) \nLet us run again')
        # Need this error to stop from flushing directory
        return
    else:
        shutil.make_archive(f_name, 'tar', base_dir=dest_dir)
        print('Files have been compressed')
        print('Beamline scientist can decide if files under %s '
              'are going to be kept' % src_dir)
        os.chdir(cwd)


def export_data(root_dir=None, ar_format='gztar'):
    """Create a tarball of all of the data is the user folders.

    This assumes that the root directory is layed out prescribed by DataPath.

    This function will:

      - remove any existing tarball
      - create a new (timestamped) tarball

    """
    if root_dir is None:
        root_dir = B_DIR
    dp = DataPath(root_dir)
    # remove any existing exports
    shutil.rmtree(dp.export_dir)
    # tiff name
    print('Deleting any existing archive files in the Export directory')
    f_name = strftime('data4export_%Y-%m-%dT%H%M')
    os.makedirs(dp.export_dir)
    cur_path = os.getcwd()
    try:
        os.chdir(dp.stem)
        tar_return = shutil.make_archive(f_name, ar_format,
                                         root_dir=dp.stem,
                                         base_dir='xpdUser',
                                         verbose=1, dry_run=False)
        shutil.move(tar_return, dp.export_dir)
    finally:
        os.chdir(cur_path)
    out_file = os.path.join(dp.export_dir, tar_return)
    print('New archive file with name '+out_file+' written.')
    print('Please copy this to your local computer or external hard-drive')


def start_beamtime(base_dir=None):
    if base_dir is None:
        base_dir = B_DIR
    datapath = DataPath(base_dir)
    print(datapath)
    _make_clean_env(datapath)
    _ensure_empty_datapaths(datapath)
    _setup_config(datapath)
    return

"""
def end_beamtime(base_dir=B_DIR):
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc., and archives them to a
    directory in the remote file-store with filename B_DIR/useriD

    '''
    import shutil

    datapath = DataPath(base_dir)

    #FIXME - a way to confirm SAF_number in current md_class
    #SAF_num = metadata['SAF_number']
    #userID = SAF_num
    #userIn = input('SAF number to current experiment is %s. Is it correct (y/n)? ' % SAF_num)
    #if userIn not in ('y','yes',''):
        #print('Alright, lets do it again...')
        #return

    if os.path.isdir(B_DIR):
        pass
    else:
        os.makedirs(B_DIR)

    saf_num = input('Please enter your SAF number to this beamtime: ')

    PI_name = input('Please enter PI name to this beamtime: ')

    time_info = _get_time(date = False)

    full_info = '_'.join([PI_name.strip(), saf_num.strip(), time_info.strip()])

    backup_f_name = os.path.join(B_DIR, full_info)

    print('Current data in subdirectories under xpdUser/ will be compressed and moved to %s' % B_DIR)

    if os.path.isfile(backup_f_name):
        print('a file with the same PI name, SAF number and year-month already exists')
        print('before proceeding, check that you entered the correct information')
        print('do you want to create a new backup file for a new beamtime with this user?')
        print('to add files to the existing backup directory hit return.')
        respo = input('Otherwise, enter a new directory name, e.g., "secondbeamtime":')
        if str(respo) != '':
            new_name = os.path.join(B_DIR, full_info + '_' + str(respo))
            backup_f_name = new_name
        else:
            print('continue...')

    _tar_n_move(backup_f_name, src_dir = datapath.base, dest_dir = B_DIR)
    flush_dir(datapath.import_dir)

"""
