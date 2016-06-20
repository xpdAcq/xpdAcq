import os
import sys
import shutil
from shutil import ReadError
import tarfile as tar
from time import strftime

def _graceful_exit(error_message):
    try:
        raise RuntimeError(error_message)
        return 0
    except Exception as err:
        sys.stderr.write('WHOOPS: {}'.format(str(err)))
        return 1


def composition_analysis(compstring):
    """Pulls out elements and their ratios from the config file.

    compstring   -- chemical composition of the sample, e.g.,
                    "NaCl", "H2SO4", "La0.5 Ca0.5 Mn O3".  Blank
                    characters are ignored, unit counts can be omitted.
                    It is critical to use proper upper-lower case for atom
                    symbols as this is used to delimit them in the formula.

    Returns a list of atom symbols and a corresponding list of their counts.
    """
    import re
    # remove all blanks
    compbare = re.sub('\s', '', compstring)
    # reusable error message
    # make sure there is at least one uppercase character in the compstring
    upcasechars = any(str.isupper(c) for c in compbare)
    if not upcasechars and compbare:
        emsg = 'invalid chemical composition "%s"' % compstring
        raise ValueError(emsg)
    # split at every upper-case letter, possibly followed by a lower case
    # one and charge specification
    namefracs = re.split('([A-Z][a-z]?(?:[1-8]?[+-])?)', compbare)[1:]
    names = namefracs[0::2]
    # use unit count when empty, convert to float otherwise
    getfraction = lambda s: (s == '' and 1.0 or float(s))
    fractions = [getfraction(w) for w in namefracs[1::2]]
    return names, fractions


def export_userScriptsEtc():
    """ function that exports user defined objects/scripts stored under config_base and userScript
        
        it will create a uncompressed tarball inside xpdUser/Export

    Return
    ------
        archive_path : str
        path to archive file just created
    """
    F_EXT = '.tar'
    root_dir = glbl.home
    os.chdir(root_dir)
    f_name = strftime('userScriptsEtc_%Y-%m-%dT%H%M') + F_EXT
    # extra work to avoid comple directory structure in tarball
    tar_f_name = os.path.join(glbl.home, f_name)
    export_dir_list = list(map(lambda x: os.path.basename(x), glbl._export_tar_dir))
    with tar.open(tar_f_name, 'w') as f:
        for el in export_dir_list:
            f.add(el)
    archive_path = os.path.join(glbl.home, f_name)
    if os.path.isfile(archive_path):
        return archive_path
    else:
        _graceful_exit('Did you accidentally change write privilege to {}'.format(glbl.home))
        print('Please check your setting and try `export_userScriptsEtc()` again at command prompt')
        return


def import_userScriptsEtc():
    '''Import user files that have been placed in xpdUser/Import for use by xpdAcq

    Allowed files are python user-script files (extension .py), detector-image mask files (.npy) or files containing xpdAcq objects (extension .yml).
    Files created by running export_userScriptsEtc() are also allowed.  Unallowed files (anything not in the previous list) will be ignored. 

    After import, all files in the xpdUser/import directory will be deleted
    The user can run `export_userScriptsEtc` to revert them.

    Return
    ------
        moved_list : list
        a list of file names that have been moved successfully
    '''
    _f_ext_dst_dict = ['py', 'npy', 'yml']
    src_dir = glbl.import_dir
    f_list = os.listdir(src_dir)
    if len(f_list) == 0:
        print('INFO: There is no predefined user objects in {}'.format(src_dir))
        return 
    # unpack every archived file in Import/
    for f in f_list:
        try:
            # shutil should handle all compressed cases
            tar_full_path = os.path.join(src_dir, f)
            shutil.unpack_archive(tar_full_path, src_dir)
        except ReadError:
            pass
    f_list = os.listdir(src_dir) # new f_list, after unpack
    moved_list = []
    failure_list = []
    for f_name in f_list:
        if os.path.isfile(os.path.join(src_dir, f_name)):
            src_full_path = os.path.join(src_dir, f_name)
            (root, ext) = os.path.splitext(f_name)
            if ext == '.yml':
                dst_dir = glbl.yaml_dir
                yml_dst_name = _copy_and_delete(f_name, src_full_path, dst_dir)
                moved_list.append(yml_dst_name)
            elif ext == '.py':
                dst_dir = glbl.usrScript_dir
                py_dst_name = _copy_and_delete(f_name, src_full_path, dst_dir) 
                moved_list.append(py_dst_name)
            elif ext == '.npy':
                dst_dir = glbl.config_base
                npy_dst_name = _copy_and_delete(f_name, src_full_path, dst_dir) 
                moved_list.append(npy_dst_name)
            elif ext in ('.tar', '.zip', '.gztar'):
                pass
            else:
                print('{} is not a supported format'.format(f_name))
                failure_list.append(f_name)
                pass
        else:
            # don't expect user to have directory
            print('''I can only import files, not directories. Please place in the import directory either:
                (1) all your files such as scripts, masks and xpdAcq object yaml files or 
                (2) a tar or zipped-tar archive file containing those files.'''.format(f_name))
            failure_list.append(f_name)
            pass
    if failure_list:
        print('Finished importing. Failed to move {} but they will leave in Import/'.format(failure_list))
    return moved_list

def _copy_and_delete(f_name, src_full_path, dst_dir):
    shutil.copy(src_full_path, dst_dir)
    dst_name = os.path.join(dst_dir, f_name) 
    if os.path.isfile(dst_name):
        print('{} has been successfully moved to {}'.format(f_name, dst_dir))
        os.remove(src_full_path)
        return dst_name
    else:
        print('''We had a problem moving {}.
                Most likely it is not a supported file type (e.g., .yml, .py, .npy, .tar, .gz).
                It will not be available for use in xpdAcq, but it will be left in the xpdUser/Import/ directory'''.            format(f_name))
        return

