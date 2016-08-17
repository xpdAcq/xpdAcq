import os
import sys
import yaml
import shutil
import tarfile as tar
from time import strftime
from shutil import ReadError

import pandas as pd

from .glbl import glbl
from .beamtime import Sample

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



class ExceltoYaml:
    # maintain in place
    NAME_FIELD= ['Collaborator']
    SAMPLE_FIELD = ['Sample Info']

    # reference
    MAPPING = {'composition_dict': 'sa_composition',
               'phase_dict': 'sa_phase',
               'Collaborator': 'ex_collaborator',
               'Experiment Name': 'ex_name',
               'Experiment Type' : 'ex_type',
               'Geometry': 'ex_geometry',
               'Structure Info': 'sa_structure_info'}

    def __init__(self):
        self.pd_dict = None
        self.sa_md_list = None

    def load(self, saf_num):
        xl_f = [f for f in os.listdir(glbl.xpdconfig) if
                f.startswith(str(saf_num)+'_sample')]
        if not xl_f:
            raise FileNotFoundError("assigned file doesn't exist")
        if len(xl_f) >1:
            raise ValueError("Found more than one file, please make sure"
                             "there is only one in {}"
                             .format(glbl.xpdconfig))
        self.pd_dict = pd.read_excel(os.path.join(glbl.xpdconfig,
                                                  xl_f.pop()))

        self.sa_md_list = self._pd_dict_to_dict_list(self.pd_dict.to_dict())

    def create_yaml(self, bt):
        """ parse a list of sample metadata into desired format and
        create xpdacq.Sample objects inside xpdUser/config_base/yml/

        Parameters
        ----------
        bt : xpdacq.Beamtime object
            an object carries SAF, PI_last and other information

        Returns
        -------
        None
        """

        parsed_sa_md_list = []
        for sa_md in self.sa_md_list:
            parsed_sa_md = {}
            for k, v in sa_md.items():
                mapped_key = self.MAPPING.get(k, None)
                # name field
                if k in self.NAME_FIELD:
                    #print('Parsing name')
                    try:
                        parsed_val = self._name_parser(v)
                        #print("successfully parsed name {} -> {}"
                        #      .format(v, parsed_val))
                    except ValueError:
                        parsed_val = v
                        #print('cant parsed {}'.format(v))
                    parsed_sa_md.update({mapped_key:parsed_val})

                # special case
                elif k in self.SAMPLE_FIELD:
                    try:
                        composition_dict, phase_dict = self._phase_parser(v)
                    except ValueError:
                        composition_dict = v
                        phase_dict = v
                    finally:
                        parsed_sa_md.update({self.MAPPING['composition_dict']:
                                             composition_dict})

                        parsed_sa_md.update({self.MAPPING['phase_dict']:
                                             phase_dict})
                        # restructure sa_name
                        v = v.replace(' ', '')
                        v = v.replace(':','_')
                        v = v.replace(',', '_')
                        parsed_sa_md.update({'sa_name':v})

                # other fields dont need to be pased
                else:
                    #print('update {}->{}:{}'.format(k, mapped_key, v))
                    if mapped_key is not None:
                        parsed_sa_md.update({mapped_key:v.replace(' ','_')})
                    else:
                        parsed_sa_md.update({k:v.replace(' ', '_')})

            parsed_sa_md_list.append(parsed_sa_md)
        self.parsed_sa_md_list = parsed_sa_md_list

        for el in self.parsed_sa_md_list:
            sa_name = el['sa_name']
            Sample(bt, el)
            print("Sample object {} has been successfully imported"
                  .format(sa_name))
        print("*** End of import Sample object ***")

    def _pd_dict_to_dict_list(self, pd_dict):
        """ parser of pd generated dict to a list of valid sample dicts

        Parameters
        ----------
        pd_dict : dict
            dict generated from pandas.to_dict method

        Return:
        -------
        sa_md_list : list
            a list of dictionaries. Each element is a sample dictionary
        """

        row_num = len(list(pd_dict.values())[0])
        sa_md_list = []
        for i in range(row_num):
            sa_md = {}
            for key in pd_dict.keys():
                sa_md.update({key:pd_dict[key][i]})
            sa_md_list.append(sa_md)

        return sa_md_list


    def _name_parser(self, name_str):
        """ parser for field specified names

        Parameters
        ----------
        name_str : str
            a string contains a series of <first_name  last_name> of a human.
            Each human is separated by a comma.

        Returns
        -------
        name_list : list
            a list contains first and last names.

        Raises:
        -------
        ValueError
            if ',' is not specified between names
        """
        name_list = []
        persons = name_str.split(',')
        for el in persons:
            first, last = el.strip().split(' ')
            name_list.append(first)
            name_list.append(last)

        return name_list


    def _phase_parser(self, phase_str):
        """ parser for filed with <chem formular>: <phase_amount>

        Parameters
        ----------
        phase_str : str
            a string contains a series of <chem formular> : <phase_amount>.
            Each phase is separated by a comma

        Returns
        -------
        composition_dict : dict
            a dictionary contains {element: stoichiometry}
        phase_dict : dict
            a dictionary contains relative ratio of phases

        Examples
        --------
        rv = _phase_parser('NaCl:1, Si:1')
        rv[0] # {'Na':1, 'Cl':1, 'Si':1}
        rv[1] # {'Nacl':0.5, 'Si':0.5}

        Raises:
        -------
        ValueError
            if ',' is not specified between phases
        """

        phase_dict = {}
        composition_dict = {}
        compound_meta = phase_str.split(',')
        for el in compound_meta:
            if len(el.split(':')) == 1:
                com = el.split(':').pop()
                amount = '1' # capture default
            else:
                com, amount = el.split(':') # expect [<com>, <amount>]
            phase_dict.update({com.strip():float(amount.strip())})
            parsed_tuple = composition_analysis(com.strip())
            # expect: ([elment_1, element_2, ...], [sto_1, sto_2,...])
            for i in range(len(parsed_tuple[0])):
                composition_dict.update({parsed_tuple[0][i]:
                                         parsed_tuple[1][i]})
        # normalized phase_dict
        total = sum(phase_dict.values())
        for k,v in phase_dict.items():
            ratio = "{0:.2f}".format(v/total)
            phase_dict[k] = float(ratio)
        return composition_dict, phase_dict

excel_to_yaml = ExceltoYaml()

def import_sample(saf_num, bt):
    """ thing wrapper for ExceltoYaml class """
    excel_to_yaml.load(str(saf_num))
    excel_to_yaml.create_yaml(bt)
    return excel_to_yaml
