import os
import sys
import shutil
import tarfile as tar
from time import strftime

from xpdacq.glbl import glbl
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

def _RE_state_wrapper(RE_obj):
    ''' a wrapper to check state of bluesky runengine object after pausing

        it provides control to stop/abort/resume runengine under current package structure
    '''
    usr_input = input('')
    # while loop gives chance to iteratively confirm user's input
    while RE_obj.state == 'paused':
        if usr_input in ('resume()'):
            RE_obj.resume()
        elif usr_input in ('abort()'):
            abort_all = input('''current scan will be aborted. Do you want to abort all successive scans (if you are running a script)? y/[n]  ''')
            while True:
                if abort_all in ('y', 'yes'):
                    sys.exit(_graceful_exit('''INFO: All successive scans are aborted'''))
                elif abort_all in ('n', 'no'):
                    print('''INFO: Current scan is aborted and successive ones are kept''')
                    RE_obj.abort()
                else:
                    print('please reenter your input')
        elif usr_input in ('stop()'):
            RE_obj.stop()
        else:
            print('please renter your input')

def export_userScriptEtc():
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
    f_name = strftime('userScriptEtc_%Y-%m-%dT%H%M') + F_EXT
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
        print('Please check your setting and try `export_userScriptEtc()` again at command prompt')
        return

def import_userScriptEtc():
    '''
    import beamtime control files predefined by users from xpdUser/Import

    Files could be archived files or indivisual script(.py), mask(.npy) or yaml(.yml) files.
    Once files are imported, they will be deleted but user can use `export_userScriptEtc` to revert them.
    '''
    _f_ext_dst_dict = ['py', 'npy', 'yml']
    src_dir = glbl.import_dir
    f_list = os.listdir(src_dir)
    if len(f_list) == 0:
        print('INFO: There is no pre-defined user objects in {}'.format(src_dir))
        return 
    # unpack every archived file in Import/
    for f in f_list:
        try:
            # shutil should handle all compressed cases
            shutil.unpack_archive(src_full_path, src_dir)
        except ReadError:
            pass
    f_list = os.listdir(src_dir) # new f_list, after unpack
    moved_list = []
    failure_list = []
    for f_name in f_list:
        if os.path.isfile(f_name):
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
            else:
                print('{} is not a supported format'.format(f_name))
                failure_list.append(f_name)
                pass
        else:
            # don't expect user to see have directory
            print('Expect a file but get a directory {}. Did you properly archive it?'.format(f_name))
            failure_list.append(f_name)
            pass
    print('Finished importing. Failed to move {} but they will leave in Import/'.format(failure_list))
    return moved_list

def _copy_and_delete(f_name, src_full_path, dst_dir):
    shutil.copy(src_full_path, dst_dir)
    dst_name = os.path.join(dst_dir, f_name) 
    if os.path.isfile(dst_name):
        print('{} has been successfully moved to {}'.format(f_name, dst_dir))
        os.remove(full_path)
        return dst_name
    else:
        print('We have problem moving {}. It will still leave at xpdUser/Import/'.format(f_name))
        return

