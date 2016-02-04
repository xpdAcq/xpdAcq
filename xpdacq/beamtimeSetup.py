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

B_DIR = os.getcwd()

from time import strftime

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



def _end_beamtime(base_dir=None, archive_dir=None):
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
        archive_dir = os.path.expanduser(strftime('~/pe1_data/userfiles/%Y'))

    if base_dir is None:
        base_dir = B_DIR
    dp = DataPath(base_dir)
    tar_ball = export_data(base_dir)
    ext = get_full_ext(tar_ball)
    os.makedirs(archive_dir, exist_ok=True)
    try:
        saf_num = bt.md['bt_safN']
        PI_name = bt.md['bt_piLast']
    except NameError:
        saf_num = input('Please enter your SAF number to this beamtime: ')
        PI_name = input('Please enter PI name to this beamtime: ')

    full_info = '_'.join([PI_name.strip().replace(' ', ''),
                          saf_num.strip()])

    archive_f_name = os.path.join(archive_dir, full_info) + ext
    shutil.copyfile(tar_ball, archive_f_name)
    shutil.rmtree(dp.base)
    os.makedirs(dp.base)
    shutil.copy(archive_f_name, dp.base)
    final_path = os.path.join(dp.base, os.path.basename(archive_f_name))
    print("Final archive file at {}".format(final_path))
    return final_path


def get_full_ext(path, post_ext=''):
    path, ext = os.path.splitext(path)
    if ext:
        return get_full_ext(path, ext + post_ext)
    return post_ext


def _start_beamtime(base_dir=None):
    if base_dir is None:
        base_dir = B_DIR
    dp = DataPath(base_dir)
    if os.path.exists(dp.base):
        if not os.path.isdir(dp.base):
            raise RuntimeError("Expected a folder, got a file.  "
                               "Talk to beamline staff")
        files = os.listdir(dp.base)
        if len(files) > 1:
            raise RuntimeError("Unexpected files in {}, you need to run"
                               "Talk to beamline staff".format(dp.base))
        elif len(files) == 1:
            tf, = files
            if 'tar' not in tf:
                raise RuntimeError("Expected a tarball of some sort, found {} "
                                   "Talk to beamline staff"
                                   .format(tf))
            os.unlink(os.path.join(dp.base, tf))

    _make_clean_env(dp)
    saf_num = input('Please enter your SAF number to this beamtime: ')
    PI_name = input('Please enter PI name to this beamtime: ')
    bt = Beamtime(PI_name,saf_num)
    return
