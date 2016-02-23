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
import sys
from xpdacq.config import DataPath


class XPD:

    def _getuid(self):
        return str(uuid.uuid1())

    def export(self):
        return self.md
    
    def _yaml_path(self):
        self.yaml_dir_path = os.path.join(self._base_path, 'config_base', 'yml')
        os.makedirs(self.yaml_dir_path, exist_ok = True) 
        return self.yaml_dir_path

    def _yaml_garage_path(self):
        self.yaml_garage_dir_path = os.path.join(self._base_path, 'config_base', 'yml_garage')
        os.makedirs(self.yaml_garage_dir_path, exist_ok = True)
        # backup directory when user wants to move out objects from default reading list
        return self.yaml_garage_dir_path

                    
    def _yamify(self):
        '''write a yaml file for this object and place it in config_base/yml'''
        fname = self.name
        ftype = self.type
        fpath = os.path.join(self._yaml_path(), str(ftype) +'_'+ str(fname) +'.yml')
        if isinstance(fpath, str):
            with open(fpath, 'w') as fout:
                yaml.dump(self, fout)
        else:
            yaml.dump(self, fpath)

    @classmethod
    def _get_ymls(cls):
        fpath = cls._yaml_path(cls)
        yamls = os.listdir(fpath)
        return yamls

    @classmethod
    def loadyamls(cls):
        fpath = cls._yaml_path(cls)
        yamls = os.listdir(fpath)
        olist = []
        for f in yamls:
            fname = os.path.join(fpath,f)
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
                print(i.type+' object '+str(i.name)+' has list index ', iter-1)
        else:
            iter = 0
            for i in list:
                iter += 1
                if i.type == type:
                    print(i.type+' object '+str(i.name)+' has list index ', iter-1)
        print('Use bt.get(index) to get the one you want')

    @classmethod
    def get(cls, index):
        list = cls.loadyamls()
        return list[index]

    @classmethod
    def remove(cls, index):
        garage_path = cls._yaml_garage_path(cls)
        read_path = cls._yaml_path(cls)

        list = cls.loadyamls()
        obj_name = list[index].name
        obj_type = list[index].type
        f_name = os.path.join(read_path, obj_type+'_'+obj_name+'.yml')

        print("You are about to remove %s object with name %s from current object list" % (obj_type, obj_name))
        user_confirm = input("Do you want to continue y/[n]: ")
        if user_confirm in ('y','Y'):
            shutil.move(f_name, garage_path)
        else:
            return
    
class Beamtime(XPD):
    def __init__(self, pi_last, safn, wavelength, experimenters = [], base_dir=None,**kwargs):
        if not base_dir:
            dp = DataPath(os.path.expanduser('~'))
            self._base_path = dp.base
        else:
            self._base_path = base_dir
        self.name = 'bt'
        self.type = 'bt'
        self.md = {'bt_piLast': _clean_md_input(pi_last), 'bt_safN': _clean_md_input(safn), 
                    'bt_usermd':_clean_md_input(kwargs)}
        self.md.update({'bt_wavelength': _clean_md_input(wavelength)})
        self.md.update({'bt_experimenters': _clean_md_input(experimenters)})
        self.md.update({'bt_uid': self._getuid()})
        self._yamify()


class Experiment(XPD):
    def __init__(self, expname, beamtime, **kwargs):
        self.name = _clean_md_input(expname)
        self.type = 'ex'
        self.bt = beamtime
        self.md = self.bt.md
        self.md.update({'ex_name': self.name})
        self.md.update({'ex_uid': self._getuid()})
        self.md.update({'ex_usermd':_clean_md_input(kwargs)})
        self._yamify()

class Sample(XPD):
    def __init__(self, samname, experiment, **kwargs):
        self.name = _clean_md_input(samname)
        self.type = 'sa'
        self.ex = experiment
        self.md = self.ex.md
        self.md.update({'sa_name': self.name})
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
           delay time between exposures in a tseries. In Tramps as well as 'exposure' 
           the required keys are 'Tstart', 'Tstop', 'Tstep'.
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
        self.sc_params = scan_params # sc_parms is a dictionary
        
        self._plan_validator()
        
        self.shutter = shutter
        self.md = {}
        self.md.update({'sc_name': _clean_md_input(self.name)})
        self.md.update({'sc_type': _clean_md_input(self.scan)})
        self.md.update({'sc_uid': self._getuid()})
        self.md.update({'sc_usermd':_clean_md_input(kwargs)})
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

    #FIXME - make validator clean later
    def _plan_validator(self):
        ''' Validator for ScanPlan object
        
        It validates if required scan parameters for certain scan type are properly defined in object

        Parameters
        ----------
            scan_type : str
                scan tyoe of XPD Scan object
        '''
        # based on structures in xpdacq.xpdacq.py
        _Tramp_required_params = ['startingT', 'endingT', 'requested_Tstep', 'exposure']
        _Tramp_optional_params = ['det', 'subs_dict']

        _ct_required_params = ['exposure']
        _ct_optional_params = ['det','subs_dict'] 
        # leave optional parameter list here, in case we need to use them in the future
        
        
        # params in tseries is not completely finalized
        _tseries_required_params = ['exposure', 'delay', 'num']
        
        if self.scan == 'ct':
            for el in _ct_required_params:
                try:
                    self.sc_params[el]
                except KeyError:
                    print('It seems you are using a Count scan but the scan_params dictionary does not contain {}  which is needed.'.format(el))
                    print('Please use uparrow to edit and retry making your ScanPlan object')
                    sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')

        elif self.scan == 'Tramp':
            for el in _Tramp_required_params:
                try:
                   self.sc_params[el]
                except KeyError:
                   print('It seems you are using a temperature ramp scan but the scan_params dictionary does not contain {} which is needed.'.format(el))
                   print('Please use uparrow to edit and retry making your ScanPlan object')
                   sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')
        
        elif self.scan == 'tseries':
           for el in _tseries_required_params:
               try:
                   self.sc_params[el]
               except KeyError:
                   print('It seems you are using a tseries scan but the scan_params dictionary does not contain {} which is needed.'.format(el))
                   print('Please use uparrow to edit and retry making your ScanPlan object')
                   sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')
        else:
            print('It seems you are defining an unknown scan')
            print('Please use uparrow to edit and retry making your ScanPlan object')
            sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')

        ''' bad logic, will be discarded
        if self.scan == 'ct':
            if list(self.sc_params.keys()) == _ct_required_params:
                pass
            else:
                extra_sc_params = list()
                for el in list(self.sc_params.keys()):
                    if el not in _ct_required_params:
                        extra_sc_params.append(el)
                if extra_sc_params:
                    print('It seems you are using a Count scan but the scan_params dictionary contain extra parameters {}'.format(extra_sc_params))

                required_sc_params = list()
                for el in _ct_required_params:
                    try:
                        self.sc_params[el]
                    except KeyError:
                        required_sc_params.append(el)
                if required_sc_params:
                    print('It seems you are using a Count scan but the scan_params dictionary doesn not contain {} which is needed'.format(required_sc_params))
                
                print('Please use uparrow to edit and retry making your ScanPlan object')
                sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')

        elif self.scan == 'Tramp':
            if list(self.sc_params.keys()) == _Tramp_required_params:
                pass
            else:
                extra_sc_params = list()
                for el in list(self.sc_params.keys()):
                    if el not in _Tramp_required_params:
                        extra_sc_params.append(el)
                if extra_sc_params:
                    print('It seems you are using a Tramp scan but the scan_params dictionary contain extra parameters {}'.format(extra_sc_params))

                required_sc_params = list()
                for el in _Tramp_required_params:
                    try:
                        self.sc_params[el]
                    except KeyError:
                        required_sc_params.append(el)
                if required_sc_params:
                    print('It seems you are using a Tramp scan but the scan_params dictionary doesn not contain {} which is needed'.format(required_sc_params))
                
                print('Please use uparrow to edit and retry making your ScanPlan object')
                sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')
                   
        elif self.scan == 'tseries':
            if list(self.sc_params.keys()) == _tseries_required_params:
                pass
            else:
                extra_sc_params = list()
                for el in list(self.sc_params.keys()):
                    if el not in _tseries_required_params:
                        extra_sc_params.append(el)
                if extra_sc_params:
                    print('It seems you are using a tseries scan but the scan_params dictionary contain extra parameters {}'.format(extra_sc_params))

                required_sc_params = list()
                for el in _tseries_required_params:
                    try:
                        self.sc_params[el]
                    except KeyError:
                        required_sc_params.append(el)
                if required_sc_params:
                    print('It seems you are using a tseries scan but the scan_params dictionary doesn not contain {} which is needed'.format(required_sc_params))
                
                print('Please use uparrow to edit and retry making your ScanPlan object')
                sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')
        '''
        

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

def export_data(root_dir=None, ar_format='gztar', end_beamtime=False):
    """Create a tarball of all of the data in the user folders.

    This assumes that the root directory is laid out prescribed by DataPath.

    This function will:

      - remove any existing tarball
      - create a new (timestamped) tarball

    """
    # FIXME - test purpose
    B_DIR = os.path.expanduser('~')
    if root_dir is None:
        root_dir = B_DIR
    dp = DataPath(root_dir)
    # remove any existing exports
    if os.path.isdir(dp.export_dir):
        shutil.rmtree(dp.export_dir)
    f_name = strftime('data4export_%Y-%m-%dT%H%M')
    os.makedirs(dp.export_dir, exist_ok=True)
    cur_path = os.getcwd()
    try:
        os.chdir(dp.stem)
        print('Compressing your data now. That may take several minutes, please be patient :)' )
        tar_return = shutil.make_archive(f_name, ar_format, root_dir=dp.stem,
                base_dir='xpdUser', verbose=1, dry_run=False)
        shutil.move(tar_return, dp.export_dir)
    finally:
        os.chdir(cur_path)
    out_file = os.path.join(dp.export_dir, os.path.basename(tar_return))
    if not end_beamtime:
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


def new_exp():

    return _execute_new_exp()

def _execute_new_exp(expnam,btobj):
    pass

