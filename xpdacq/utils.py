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
    os.makedirs(glbl.export_dir, exist_ok = True)
    (dir_head, dir_tail) = os.path.split(glbl.export_dir)
    tar_f_name = os.path.join(dir_tail, f_name)
    export_dir_list = list(map(lambda x: os.path.basename(x), glbl._export_tar_dir))
    with tar.open(tar_f_name, 'w') as f:
        for el in export_dir_list:
            f.add(el)
    archive_path = os.path.join(glbl.export_dir, f_name)
    if os.path.isfile(archive_path):
        return archive_path
    else:
        _graceful_exit('Did you accidentally change write privilege to {}'.format(glbl.export_dir))
        print('Please try `export_usermetadata()` again at command prompt')
        return
