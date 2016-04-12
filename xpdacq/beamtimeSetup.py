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
from xpdacq.beamtime import export_data, _clean_md_input, _get_hidden_list
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

def _end_beamtime(base_dir=None,archive_dir=None,bto=None, usr_confirm = 'y'):
    _required_bt_info = ['bt_piLast', 'bt_safN', 'bt_uid']
    if archive_dir is None:
        archive_dir = glbl.archive_dir
    if base_dir is None:
        base_dir = glbl.base
    os.makedirs(glbl.home, exist_ok = True)
    # check env
    files = os.listdir(glbl.home)
    if len(files)==0:
        sys.exit(_graceful_exit('It appears that end_beamtime may have been run.  If so, do not run again but proceed to _start_beamtime'))
    # laod bt yaml
    if not bto: 
        bto = _load_bt(glbl.yaml_dir)
    try:
        bt_md = bto.md
    except AttributeError:
        # worst situation, user didn't even instantiate bt object with xpdAcq
        _graceful_exit('''There is no metadata attribute in beamtime object "{}".
                        User might have gone throgh entirely different workflow.
                        Reconmend to contact user before executing end_beamtime''')
    if 'bt_piLast' in bt_md.keys():
        piname = bto.md['bt_piLast']
    else:
        piname = input('Please enter PI last name for this beamtime: ')
    if 'bt_safN' in bt.md.keys():
        safn = bto.md['bt_safN']
    else:
        safn = input('Please enter your SAF number to this beamtime: ')
    if 'bt_uid' in bt.md.keys():
        btuid = bto.md['bt_uid'][:7]
    else:
        btuid = ''
    archive_full_name = _execute_end_beamtime(piname, safn, btuid, base_dir)
    _confirm_archive(archive_full_name)
    _delete_home_dir_tree(base_dir, bto)


def _load_bt(bt_yaml_path):
    btoname = os.path.join(glbl.yaml_dir,'bt_bt.yml')
    if not os.path.isfile(btoname):
        sys.exit(_graceful_exit('''{} does not exist in {}. User might have deleted it accidentally.
Please create it based on user information or contect user'''.format(os.path.basename(btoname), glbl.yaml_dir)))
    with open(btoname, 'r') as fi:
        bto = yaml.load(fi)
    return bto
    
def _tar_user_data(archive_name, root_dir = None, archive_format ='tar'):
    """ Create a remote tarball of all user folders under xpdUser directory
    """
    archive_full_name = os.path.join(glbl.archive_dir, archive_name)
    if root_dir is None:
        root_dir = glbl.base
    cur_path = os.getcwd()
    try:
        os.chdir(glbl.base)
        print('Archiving your data now. That may take several minutes, please be patient :)' )
        tar_return = shutil.make_archive(archive_full_name, archive_format, root_dir=glbl.base,
                base_dir='xpdUser', verbose=1, dry_run=False)
    finally:
        os.chdir(cur_path)
    return archive_full_name

def _execute_end_beamtime(piname, safn, btuid, base_dir):
    '''cleans up at the end of a beamtime

    Function takes all the user-generated tifs and config files, etc.,
    and archives them to a directory in the remote file-store with
    filename B_DIR/useriD

    This function does three things:

      1. runs export_data to get all of the current data
      2. copies the tarball off to an archive location
      3. removes all the un-tarred data

    '''
    os.makedirs(glbl.archive_dir, exist_ok=True)
    archive_name = '_'.join([piname.strip().replace(' ', ''),
                            str(safn).strip(), strftime('%Y-%m-%d-%H%M'), btuid]
                            )
    archive_full_name = _tar_user_data(archive_name)
    return archive_full_name

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

def _delete_home_dir_tree(base_dir, bto):
    os.chdir(glbl.base) # move out from xpdUser before deletion
    shutil.rmtree(glbl.home)
    os.makedirs(glbl.home, exist_ok=True)
    os.chdir(glbl.home)  # now move back into xpdUser
    return

def get_full_ext(path, post_ext=''):
    path, ext = os.path.splitext(path)
    if ext:
        return get_full_ext(path, ext + post_ext)
    return post_ext

def _check_empty_environment(base_dir=None):
    if base_dir is None:
        base_dir = glbl.base
    if os.path.exists(home_dir):
        if not os.path.isdir(home_dir):
            sys.exit(_graceful_exit("Expected a folder, got a file.  "
                               "Please Talk to beamline staff"))
        files = os.listdir(home_dir) # that also list dirs that have been created
        if len(files) > 0:
            sys.exit(_graceful_exit("Unexpected files in {}, you need to run _end_beamtime(). Please Talk to beamline staff".format(home_dir)))
    else:
        sys.exit(_graceful_exit("The xpdUser directory appears not to exist "
                               "Please Talk to beamline staff"))

def _init_dark_yaml():
    dark_scan_list = []
    with open(glbl.dk_yaml, 'w') as f:
        yaml.dump(dark_scan_list, f)

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
    _init_dark_yaml()

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
