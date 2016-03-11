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
import yaml
from time import strftime
from xpdacq.utils import _graceful_exit
from xpdacq.beamtime import Beamtime, XPD, Experiment, Sample, ScanPlan
from xpdacq.beamtime import export_data,_clean_md_input,_get_hidden_list
from xpdacq.glbl import glbl
from shutil import ReadError


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
        archive_dir = os.path.expanduser(strftime('~/pe2_data/%Y/userBeamtimeArchive'))
    if base_dir is None:
        base_dir = glbl.base
    if bto is None:
        try:
            bto = bt  # problem comes from bt only exists if _start_beamtime has been run and ipython never crash
                      # FIXME - load_yaml directly ?
        except NameError:
            bto = {}              # FIXME, temporary hack. Remove when we have object imports working properly
    #dp = DataPath(base_dir)
    files = os.listdir(glbl.home)
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
    archive_f = _execute_end_beamtime(piname, safn, btuid, base_dir, archive_dir, bto)
    _confirm_archive(archive_f)
    _delete_home_dir_tree(base_dir,archive_f, bto)

def _execute_end_beamtime(piname, safn, btuid, base_dir, archive_dir, bto):
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc.,
    and archives them to a directory in the remote file-store with
    filename B_DIR/useriD

    This function does three things:

      1. runs export_data to get all of the current data
      2. copies the tarball off to an archive location
      3. removes all the un-tarred data

    '''
    tar_ball = export_data(base_dir, end_beamtime=True)
    ext = get_full_ext(tar_ball)
    os.makedirs(archive_dir, exist_ok=True)

    full_info = '_'.join([piname.strip().replace(' ', ''),
                            str(safn).strip(), strftime('%Y-%m-%d-%H%M'), btuid]
                            )
    archive_f_name = os.path.join(archive_dir, full_info) + ext
    shutil.copyfile(tar_ball, archive_f_name) # remote archive'
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
        sys.exit(_graceful_exit('xpdUser directory delete operation cancelled at Users request'))

def _delete_home_dir_tree(base_dir, archive_f_name, bto):
    #dp = DataPath(base_dir)
    os.chdir(glbl.base)   # don't remember the name, but move up one directory out of xpdUser before deleting it!
    shutil.rmtree(glbl.home)
    os.makedirs(glbl.home, exist_ok=True)
    shutil.copy(archive_f_name, glbl.home)
    os.chdir(glbl.home)   # now move back into xpdUser so everyone is not confused....
    final_path = os.path.join(glbl.home, os.path.basename(archive_f_name)) # local archive
    #print("Final archive file at {}".format(final_path))
    return 'local copy of tarball for user: '+final_path

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
            sys.exit(_graceful_exit("Expected a folder, got a file.  "
                               "Please Talk to beamline staff"))
        files = os.listdir(home_dir) # that also list dirs that have been created
        if len(files) > 1:
            sys.exit(_graceful_exit("Unexpected files in {}, you need to run _end_beamtime(). Please Talk to beamline staff".format(home_dir)))
        elif len(files) == 1:
            tf, = files
            if 'tar' not in tf:
                sys.exit(_graceful_exit("Expected a tarball of some sort, found {} "
                                   "Please talk to beamline staff"
                                   .format(tf)))
            os.unlink(os.path.join(home_dir, tf))
    else:
        sys.exit(_graceful_exit("The xpdUser directory appears not to exist "
                               "Please Talk to beamline staff"))

def _start_beamtime(safn,home_dir=None):
    if home_dir is None:
        home_dir = glbl.home
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)
    _check_empty_environment()
    configfile = os.path.join(glbl.xpdconfig,'saf{}.yml'.format(str(safn)))
    if os.path.isfile(configfile):
        with open(configfile, 'r') as fin:
            setup_dict = yaml.load(fin)
    else:
        sys.exit(_graceful_exit('the saf config file {} appears to be missing'.format(configfile)))
    try:
        piname = setup_dict['PI last name']
        safn = setup_dict['saf number']
        explist = setup_dict['experimenter list']
    except KeyError:
        sys.exit(_graceful_exit('Cannot load input info. File syntax in {} maybe corrupted.'.format(configfile)))
    bt = _execute_start_beamtime(piname, safn, explist, home_dir=home_dir)
    return bt

def _execute_start_beamtime(piname,safn,explist,wavelength=None,home_dir=None):
    PI_name = piname
    saf_num = safn
    _make_clean_env()
    os.chdir(home_dir)
    bt = Beamtime(PI_name,saf_num,experimenters=explist)

    # now populate the database with some lazy-user objects
    ex = Experiment('l-user',bt)
    sa = Sample('l-user',ex)
    sc01 = ScanPlan('ct.1s','ct',{'exposure':0.1})
    sc05 = ScanPlan('ct.5s','ct',{'exposure':0.5})
    sc1 = ScanPlan('ct1s','ct',{'exposure':1.0})
    sc5 = ScanPlan('ct5s','ct',{'exposure':5.0})
    sc10 = ScanPlan('ct10s','ct',{'exposure':10.0})
    sc30 = ScanPlan('ct30s','ct',{'exposure':30.0})
    return bt

def import_yaml():
    '''
    import user pre-defined files from ~/xpdUser/Import

    Files can be compreesed or .yml, once imported, bt.list() should show updated acquire object list
    '''
    src_dir = glbl.import_dir
    dst_dir = glbl.yaml_dir
    f_list = os.listdir(src_dir)
    if len(f_list) == 0:
        print('INFO: There is no pre-defined user objects in {}'.format(src_dir))
        return 
    # two possibilites: .yml or compressed files; shutil should handle all compressed cases
    moved_f_list = []
    for f in f_list:
        full_path = os.path.join(src_dir, f)
        (root, ext) = os.path.splitext(f)
        if ext == '.yml':
            shutil.copy(full_path, dst_dir)
            moved_f_list.append(f)
            # FIXME - do we want user confirmation?
            os.remove(full_path)
        else:
            try:
                shutil.unpack_archive(full_path, dst_dir)
                moved_f_list.append(f)
                # FIXME - do we want user confirmation?
                os.remove(full_path)
            except ReadError:
                print('Unrecongnized file type {} is found inside {}'.format(f, src_dir))
                pass
    return moved_f_list

if __name__ == '__main__':
    print(glbl.home)
