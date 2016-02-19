#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge, Tom Caswell
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import sys
import os
import datetime
import shutil
from time import strftime
from xpdacq.config import DataPath
from xpdacq.beamtime import Beamtime, XPD
from xpdacq.beamtime import export_data
#from xpdacq.control import _get_obj

B_DIR = os.path.expanduser('~')
#def _get_obj(name):
    #ip = get_ipython() # build-in function
    #return ip.user_ns[name]

#B_DIR = _get_obj('B_DIR')


# just a note. Assign by Sanjit
REMOTE_DIR = os.path.expanduser('~/pe2_data/')
BACKUP_DIR = os.path.join(REMOTE_DIR, strftime('%Y'), 'userBeamtimeArchive')


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
    out = []
    for d in datapath.allfolders:
        os.makedirs(d, exist_ok=True)
        out.append(d)
    return out



def _end_beamtime(base_dir=B_DIR, archive_dir=None, bto = None):
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc.,
    and archives them to a directory in the remote file-store with
    filename B_DIR/useriD

    This function does three things:

      1. runs export_data to get all of the current data
      2. copies the tarball off to an archive location
      3. removes all the un-tarred data

    '''
    if archive_dir is None:
        archive_dir = os.path.expanduser(strftime('~/pe2_data/%Y/userBeamtimeArchive'))

    if base_dir is None:
        base_dir = B_DIR

    if bto is None:
        try:
            bto = bt  # problem comes from bt only exists if _start_beamtime has been run and ipython never crash
                      # FIXME - load_yaml directly ?
        except NameError:
            bto = {}              # FIXME, temporary hack. Remove when we have object imports working properly

    dp = DataPath(base_dir)
    files = os.listdir(dp.base)
    if len(files)==1:
        print('It appears that end_beamtime may have been run.  If so, do not run again but proceed to _start_beamtime')
        return

    tar_ball = export_data(base_dir, end_beamtime=True)
    ext = get_full_ext(tar_ball)
    os.makedirs(archive_dir, exist_ok=True)
    try:
        PI_name = bto.md['bt_piLast']
    except AttributeError:
        PI_name = input('Please enter PI last name for this beamtime: ')
    try:
        saf_num = bto.md['bt_safN']
    except AttributeError:
        saf_num = input('Please enter your SAF number to this beamtime: ')
    try:
        bt_uid = bto.md['bt_uid'][:7]
    except AttributeError:
        bt_uid = ''
        
    full_info = '_'.join([PI_name.strip().replace(' ', ''),
                            str(saf_num).strip(), strftime('%Y-%m-%d-%H%M'), bt_uid]
                            )
    #print('Backup your data now. It takes sometime as well, please be patient :)')
    archive_f_name = os.path.join(archive_dir, full_info) + ext
    shutil.copyfile(tar_ball, archive_f_name) # remote archive
    print("tarball archived to {}".format(archive_f_name))
    conf = input("Please confirm data are backed up. Are you ready to continue with xpdUser directory contents deletion (y,[n])?: ")
    if conf in ('y','Y'):
        pass
    else:
        return
    
    shutil.rmtree(dp.base)
    os.makedirs(dp.base, exist_ok=True)
    shutil.copy(archive_f_name, dp.base)
    final_path = os.path.join(dp.base, os.path.basename(archive_f_name)) # local archive
    #print("Final archive file at {}".format(final_path))
    
    return 'local copy of tarball for user: '+final_path


def get_full_ext(path, post_ext=''):
    path, ext = os.path.splitext(path)
    if ext:
        return get_full_ext(path, ext + post_ext)
    return post_ext

def _any_input_method(inp_func):
    return inp_func()

def _prompt_for_PIname():
    ans = _any_input_method('Please enter the PI last name to this beamtime: ')
    return ans
def _prompt_for_safN():
    ans = _any_input_method('Please enter the SAF number for this beamtime: ')
    return ans
def _prompt_for_wavelength():
    ans = _any_input_method('Please enter the x-ray wavelength: ')
    return ans
def _prompt_for_experimenters():
    print('Please enter a list of experimenters with syntax [("lastName","firstName",userID)]')
    ans = _any_input_method('default = []')
    if ans == '':
        ans = []
    return ans

def _check_empty_environment(base_dir=None):
    if base_dir is None:
        base_dir = B_DIR
    dp = DataPath(base_dir)
    if os.path.exists(dp.base):
        if not os.path.isdir(dp.base):
            raise RuntimeError("Expected a folder, got a file.  "
                               "Please Talk to beamline staff")
        files = os.listdir(dp.base) # that also list dirs that have been created
        if len(files) > 1:
            print(len(files))
            raise RuntimeError("Unexpected files in {}, you need to run _end_beamtime(). Please Talk to beamline staff".format(dp.base))
        elif len(files) == 1:
            tf, = files
            if 'tar' not in tf:
                raise RuntimeError("Expected a tarball of some sort, found {} "
                                   "Please talk to beamline staff"
                                   .format(tf))
            os.unlink(os.path.join(dp.base, tf))
    else:
        raise RuntimeError("The xpdUser directory appears not to exist "
                               "Please Talk to beamline staff")
        
def _start_beamtime(base_dir=None):
    if base_dir is None:
        base_dir = B_DIR
    _check_empty_environment(base_dir)
    PI_name = _any_input_method(_prompt_for_PIname)
    saf_num = _any_input_method(_prompt_for_safN)
    wavelength = _any_input_method(_prompt_for_wavelength)
    experimenters = _any_input_method(_prompt_for_experimenters)
    _make_clean_env(dp)
    os.chdir(dp.base)
    bt = Beamtime(PI_name,saf_num,wavelength,experimenters)
    return bt



