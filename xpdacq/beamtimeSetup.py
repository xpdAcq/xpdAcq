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
from xpdacq.beamtime import Beamtime, XPD
from xpdacq.beamtime import _clean_md_input
from xpdacq.glbl import glbl

#datapath = glbl.dp()
home_dir = glbl.home
all_folders = glbl.allfolders

def _any_input_method(inp_func):
    return inp_func()


def _make_clean_env():
    '''Make a clean environment for a new user

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
    for d in all_folders:
        os.makedirs(d, exist_ok=True)
        out.append(d)
    return out

def _end_beamtime(base_dir=None,archive_dir=None,bto=None):
    if archive_dir is None:
        archive_dir = glbl.archive_dir 
    if base_dir is None:
        base_dir = glbl.base
    if bto is None:
        try:
            bto = bt  # problem comes from bt only exists if _start_beamtime has been run and ipython never crash
                      # FIXME - load_yaml directly ?
        except NameError:
            bto = {}              # FIXME, temporary hack. Remove when we have object imports working properly
    files = os.listdir(glbl.home)

    # this logic might not be needed as we don't leave local tarball anymore
    if len(files)==1:
        print('It appears that end_beamtime may have been run.  If so, do not run again but proceed to _start_beamtime')
        return
    
    try:
        piname = bto.md['bt_piLast']
    except AttributeError:
        piname = input('Please enter PI last name for this beamtime: ')
    try:
        safn = bto.md['bt_safN']
    except AttributeError:
        safn = input('Please enter your SAF number to this beamtime: ')
    try:
        btuid = bto.md['bt_uid'][:7]
    except AttributeError:
        btuid = ''
    archive_f = _execute_end_beamtime(piname, safn, btuid, base_dir, archive_dir)
    _confirm_archive(archive_f)
    _delete_home_dir_tree(base_dir,archive_f, bto)
    
    return archive_f
    
def _execute_end_beamtime(piname, safn, btuid, base_dir, archive_dir):
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc.,
    and archives them to a directory in the remote file-store with
    filename B_DIR/useriD

    This function does three things:

      1. runs _bundle_and_archive_userarea() to get all of the current data
      2. copies the tarball off to an archive location
      3. removes all the un-tarred data

    '''
    #tar_ball = _bundle_and_archive_userarea(base_dir, end_beamtime=True)
    #ext = get_full_ext(tar_ball)
    os.makedirs(archive_dir, exist_ok=True)

    full_info = '_'.join([piname.strip().replace(' ', ''),
                            str(safn).strip(), strftime('%Y-%m-%d-%H%M'), btuid]
                            )
    archive_f_name = os.path.join(archive_dir, full_info)
    _bundle_and_archive_userarea(archive_f_name) # export data to remote drive
    #shutil.copyfile(tar_ball, archive_f_name) # remote archive
    if not os.path.isfile(archive_f_name):
        raise RuntimeError('Your remote copy is not saved properly. Please rerun _end_beamtime() again')
        # usd gracefull_warning in util laster
    return archive_f_name

def  _get_user_confirmation():
    conf = input("Please confirm data are backed up. Are you ready to continue with xpdUser directory contents deletion (y,[n])?: ")
    return conf

def _confirm_archive(archive_f_name):
    print("tarball archived to {}".format(archive_f_name))
    conf = _any_input_method(_get_user_confirmation)
    if conf in ('y','Y'):
        return
    else:
        raise RuntimeError('xpdUser directory delete operation cancelled at Users request')

def _delete_home_dir_tree(base_dir):
    #if not os.path.isdfile(archive_f_name):
        #raise FileNotFoundError ('Your remote copy does not exist, please make sure remote drive is properly mounted')
    os.chdir(glbl.base)   # don't remember the name, but move up one directory out of xpdUser before deleting it!
    shutil.rmtree(glbl.home)
    os.makedirs(glbl.home, exist_ok=True)
    #shutil.copy(archive_f_name, glbl.home)
    os.chdir(glbl.home)   # now move back into xpdUser so everyone is not confused....
    #final_path = os.path.join(glbl.home, os.path.basename(archive_f_name)) # local archive
    #print("Final archive file at {}".format(final_path))
    #return 'local copy of tarball for user: '+final_path
    return # retrun nothing

def _bundle_and_archive_userarea(archive_f_name, root_dir=None, ar_format='gztar', end_beamtime=False):
    """Create a tarball of all of the data in the user folders.

    This assumes that the root directory is laid out prescribed by DataPath.

    This function will:

      - remove any existing tarball
      - create a new (timestamped) tarball

    """
    if root_dir is None:
        root_dir = glbl.base
    #dp = DataPath(root_dir)
    # remove any existing exports
    #if os.path.isdir(glbl.export_dir):
        #shutil.rmtree(glbl.export_dir)
    #f_name = archive_f_name
    #os.makedirs(glbl.export_dir, exist_ok=True)
    cur_path = os.getcwd()
    try:
        os.chdir(glbl.base)
        print('Compressing your data now. That may take several minutes, please be patient :)' )
        tar_return = shutil.make_archive(archive_f_name, ar_format, root_dir=glbl.base,
                base_dir='xpdUser', verbose=1, dry_run=False)
        #shutil.move(tar_return, glbl.export_dir)
    finally:
        os.chdir(cur_path)
    #out_file = os.path.join(glbl.archive_dir, os.path.basename(tar_return))
    #if not end_beamtime:
        #print('New archive file with name '+out_file+' written.')
        #print('Please copy this to your local computer or external hard-drive')
    return tar_return

def get_full_ext(path, post_ext=''):
    path, ext = os.path.splitext(path)
    if ext:
        return get_full_ext(path, ext + post_ext)
    return post_ext


def _check_empty_environment(base_dir=None):
    if base_dir is None:
        base_dir = glbl.base
    #dp = DataPath(base_dir)
    if os.path.exists(home_dir):
        if not os.path.isdir(home_dir):
            raise RuntimeError("Expected a folder, got a file.  "
                               "Please Talk to beamline staff")
        files = os.listdir(home_dir) # that also list dirs that have been created
        if len(files) > 1:
            #print(len(files))
            raise RuntimeError("Unexpected files in {}, you need to run _end_beamtime(). Please Talk to beamline staff".format(home_dir))
        elif len(files) == 1:
            tf, = files
            if 'tar' not in tf:
                raise RuntimeError("Expected a tarball of some sort, found {} "
                                   "Please talk to beamline staff"
                                   .format(tf))
            os.unlink(os.path.join(home_dir, tf))
    else:
        raise RuntimeError("The xpdUser directory appears not to exist "
                               "Please Talk to beamline staff")

def _start_beamtime(home_dir=None):
    if home_dir is None:
        home_dir = glbl.home
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)
    _check_empty_environment()
    piname = input('Please enter the PI last name to this beamtime: ')
    safn = input('Please enter the SAF number for this beamtime: ')
    wavelength = input('Please enter the x-ray wavelength: ')
    print('Please enter a list of experimenters with syntax [("lastName","firstName",userID)]')
    explist = input('default = []  ')
    _explist = _clean_md_input(eval(explist))
    
    if explist == '':
        explist = []
    bt = _execute_start_beamtime(piname, safn, wavelength, _explist, home_dir)
    return bt

def _execute_start_beamtime(piname,safn,wavelength,explist,home_dir=None):
    PI_name = piname
    saf_num = safn
    wavelength = wavelength
    experimenters = explist
    _make_clean_env()
    os.chdir(home_dir)
    bt = Beamtime(PI_name,saf_num,wavelength,experimenters)
    return bt

if __name__ == '__main__':
    print(glbl.home)
