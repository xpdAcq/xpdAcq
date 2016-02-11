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
import uuid
import yaml
import os
import shutil
import datetime
from time import strftime
from xpdacq.config import DataPath


class XPD:
    _base_path = ''
    def _getuid(self):
        return str(uuid.uuid1())

#    def _gohome(self):
#        datapath = DataPath('./')
#        os.chdir(datapath.base)

    def export(self):
        return self.md
    
    def _yaml_path(self):
        yaml_dir_path = os.path.join(self._base_path, 'config_base', 'yml')
        os.makedirs(yaml_dir_path, exist_ok = True) # replace with os.makedirs function
        return yaml_dir_path

    def _yaml_garage_path(self):
        yaml_garage_dir_path = os.path.join(self._base_path, 'config_base', 'yml_garage')
        os.makedirs(yaml_garage_dir_path, exist_ok = True)
        # backup directory when user wants to move out objects from default reading list
        return yaml_garage_dir_path

                    
    def _yamify(self):
        fname = self.name
        ftype = self.type
        fpath = os.path.join(self._yaml_path(), ftype+'_'+ fname +'.yml')
        if isinstance(fpath, str):
            with open(fpath, 'w') as fout:
                yaml.dump(self, fout)
        else:
            yaml.dump(self, fpath)

    @classmethod
    def _get_ymls(cls):
        fpath = cls._yaml_path
        yamls = os.listdir(fpath)
        return yamls

    @classmethod
    def loadyamls(cls):
        fpath = cls._yaml_path(cls)
        yamls = os.listdir(fpath)
        olist = []
        for f in yamls:
            fname = fpath+f
            with open(fname, 'r') as fout:
                olist.append(yaml.load(fout))
        return olist

    @classmethod
    def list(cls, type=None):
        list = cls.loadyamls()
        if type is None:
            iter = 0
            for i in list:
                iter += 1
                print(i.type+' object '+i.name+' has list index ', iter-1)
        else:
            iter = 0
            for i in list:
                iter += 1
                if i.type == type:
                    print(i.type+' object '+i.name+' has list index ', iter-1)
        print('Use bt.get(index) to get the one you want')

    @classmethod
    def get(cls, index):
        list = cls.loadyamls()
        return list[index]

    @classmethod
    def delete(cls, index):
        garage_path = cls._yaml_garage_path(cls)
        read_path = cls._yaml_path(cls)

        list = cls.loadyamls()
        obj_name = list[index].name
        obj_type = list[index].type
        f_name = os.join(read_path, obj_type+'_'+obj_name+'.yml')

        print("You are about to remove %s object with name %s from current object list" % (obj_type, obj_name))
        user_confirm = input("Do you want to continue y/[n]: ")
        if user_confirm in ('n',''):
            print('Stopped. Nothing was removed')
            return
        elif user_confirm == 'y':
            print('Remove %s object with name %s from current object list' % (obj_type, obj_name))
            shutil.move(f_name, garage_path)

        else:
            print('Unrecongnized input, abort and not any action was taken')
            return
    
class Beamtime(XPD):
    def __init__(self, pi_last, safn, wavelength, experimenters = [], **kwargs):
        self.name = 'bt'
        self.type = 'bt'
        self.md = {'bt_piLast': _clean_md_input(pi_last), 'bt_safN': _clean_md_input(safn), 
                    'bt_usermd':_clean_md_input(kwargs)}
        self.md.update({'bt_wavelength': _clean_md_input(wavelength)})
        self.md.update({'bt_experimenters': _clean_md_input(experimenters)})
        self.md.update({'bt_uid': self._getuid()})
        self.md.update({'bt_usermd': _clean_md_input(kwargs)})
        self._yamify()

class Experiment(XPD):
    def __init__(self, expname, beamtime, **kwargs):
        self.name = _clean_md_input(expname)
        self.type = 'ex'
        self.bt = beamtime
        self.md = self.bt.md
        self.md.update({'ex_usermd':_clean_md_input(kwargs)})
        self.md.update({'ex_name': _clean_md_input(expname)})
        self.md.update({'ex_uid': self._getuid()})
        self.md.update({'ex_usermd':_clean_md_input(expname)})
        self._yamify()
        

'''
        @property
        def _private_md(self):
            retrun {}

        @property
        def md(self):
            out = {}
            out.update(self.bt.md)
            out.update(self._private_md)
            self._yamify()
'''


class Sample(XPD):
    def __init__(self, samname, experiment, **kwargs):
        self.name = _clean_md_input(samname)
        self.type = 'sa'
        self.ex = _clean_md_input(experiment)
        self.md = self.ex.md
        self.md.update({'sa_name': _clean_md_input(samname)})
        self.md.update({'sa_uid': self._getuid()})
        self.md.update({'sa_usermd': _clean_md_input(kwargs)})
        self._yamify()


class ScanPlan(XPD):
    '''ScanPlan object that defines scans to run.  To run them: prun(Sample,ScanPlan)
    
    Arguments:
    scanname - string - scan name.  Important as new scans will overwrite older
           scans with the same name.
    scan_type - string - type of scan. allowed values are 'ct','tseries', 'Tramp' 
           where  ct=count, tseries=time series (series of counts),
           and Tramp=Temperature ramp.
    scan_params - dictionary - contains all scan parameters that will be passed
           and used at run-time.  Don't make typos in the dictionary keywords
           or your scans won't work.  The list of allowed keywords is in the 
           documentation, but 'exposure' sets exposure time and is all that is needed
           for a simple count. 'num' and 'delay' are the number of images and the
           delay time between exposures in a tseries.
    shutter - bool - default=True.  If True, in-hutch fast shutter will be opened before a scan and
                closed afterwards.  Otherwise control of the shutter is left external. Set to False
                if you want to control the shutter by hand.
    livetable - bool - default=True. gives LiveTable output when True, not otherwise
    verify_write - bool - default=False.  This verifies that tiff files have been written
                   for each event.  It introduces a significant overhead so mostly used for
                   testing.
    '''
    def __init__(self,name, scan_type, scan_params, shutter=True, livetable=True, verify_write=False, **kwargs):
        self.name = _clean_md_input(name)
        self.type = 'sc'
        self.scan = _clean_md_input(scan_type)
        self.sc_params = _clean_md_input(scan_params) # sc_parms is a dictionary
        _plan_validator(self.name)

        self.shutter = shutter
        self.md = {}
        self.md.update({'sc_name': self._clean_md_input(name)})
        self.md.update({'sc_type': self._clean_md_input(type)})
        self.md.update({'sc_uid': self._getuid()})
        self.md.update({'sc_usermd':self._clean_md_input(kwargs)})
        if self.shutter: 
            self.md.update({'sc_shutter_control':'in-scan'})
        else:
            self.md.update({'sc_shutter_control':'external'})
        
        subs=[]
        if livetable: subs.append('livetable')
        if verify_write: subs.append('verify_write')
        if len(subs) > 0: scan_params.update({'subs':_clean_md_input(subs)}) 
        self.md.update({'sc_params': _clean_md_input(scan_params)})
        
        self._yamify()

class Union(XPD):
    def __init__(self,sample,scan):
        self.type = 'cmdo'
        self.sc = scan
        self.sa = sample
        self.md = self.sc.md
        self.md.update(self.sa.md)
 #       self._yamify()    # no need to yamify this

class Xposure(XPD):
    def __init__(self,scan):
        self.type = 'xp'
        self.sc = scan
        self.md = self.sc.md
 #       self._yamify()    # no need to yamify this

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
        print(dp.export_dir)
    finally:
        os.chdir(cur_path)
    out_file = os.path.join(dp.export_dir, os.path.basename(tar_return))
    print('New archive file with name '+out_file+' written.')
    print('Please copy this to your local computer or external hard-drive')
    return out_file

def _clean_md_input(obj):
    ''' strip white space '''
    if isinstance(obj, str):
        return obj.strip()
    
    elif isinstance(obj, list):
        clean_list = list()
        for el in obj:
            if isinstance(el, str):
                clean_list.append(el.strip())
            else: # if not string, just pass
                clean_list.append(el)
        return clean_list

    elif isinstance(obj, dict):
        clean_dict = dict()
        for k,v in obj.items():
            if isinstance(k, str):
                clean_key = k.strip()
            else: # if not string, just pass
                clean_key = k
            if isinstance(v, str):
                clean_val = v.strip()
            else: # if not string, just pass
                clean_val = v
            clean_dict[clean_key] = clean_val
        return clean_dict

    else:
        return obj

def _plan_validator(obj_name):
    ''' validator for ScanPlan object

    Parameters
    ----------
        obj_name : str
            name of XPD beamtime object
    '''
    # based on structures in xpdacq.xpdacq.py
    _Tseries_required_params = ['startingT', 'endingT', 'requested_Tstep', 'exposure']
    _Tseries_optional_params = ['det', 'subs_dict']

    _ct_required_params = ['exposure']
    _ct_optional_params = ['det','subs_dict'] 
    # leave optional parameter list here, in case we need to use them in the future
    
    
    # params in tseries is not completely finalized
    _tseries_required_params = ['num', 'exposure']
     
    if obj_name == 'ct':
        for el in _ct_required_params:
            try:
                sc_parms[el]
            except KeyError:
                print('It seems you are using a Count scan but you missed %s' % (el))
                print('Pleas revisit your ScanPlan object')
                return     

    if obj_name == 'Tseries':
        for el in _Tseries_required_params:
            try:
                sc_parms[el]
            except KeyError:
                print('It seems you are using a Tseries scan plan but you missed %s' % (el))
                print('Pleas revisit your ScanPlan object')
                return 

    if obj_name == 'tseries':
        for el in _tseries_required_params:
            try:
                sc_parms[el]
            except KeyError:
                print('It seems you are using a tseries scan plan but you missed %s' % (el))
                print('Pleas revisit your ScanPlan object')
                return                    
'''
class XPDSTATE():
       def __init__(self, dirpath='./config_base', md={}  ):
           self._cur_beamtime = cb
           self._cur_experiment = {}
           self._cur_sample = {}
           self._cur_scan = {}
           self._cur_exposure = {}
           self._done_measurements = []

       def start_beamtime(self, pi_last ):
           self._cur_beamtime.update({'piLast': pi_last})

       def start_expt(self, name ):
           self._cur_beamtime.update({'expName': name})

       def change_sample(self, sample_details):
           pass

       def export_for_BS(self):
           out = dict()
           out.update(self._cur_beamtime)
           out.update(self._cur_exposure)

       def export_for_testing(self):
           out = dict()
           out.update(self._cur_beamtime)
           out.update(self._cur_experiment)
           out.update(self._cur_sample)
           return out


    def export_to_yaml(self):
        pass

    @classmethod
    def from_yaml(cls, fname):
        new_state = cls('test')
        with fopen(fname) as f:
            for k, v in yaml.read(f):
                pass
'''
'''
class Beamtime(object):
    def __init__(self,piLast):
        self.beamtime_uid  = str(uuid.uuid1())
        self.piLast = piLast


    self.safn



    @property
    def beamtime_uid(self):
        return self.__beamtime_uid

    @beamtime_uid.setter
    def beamtime_uid(self,beamtime_uid):
        uid = str(uuid.uuid1())
'''
