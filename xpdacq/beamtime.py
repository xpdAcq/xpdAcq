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
import socket
from xpdacq.glbl import glbl
from xpdacq.utils import _graceful_exit

#datapath = glbl.dp()
home_dir = glbl.home
yaml_dir = glbl.yaml_dir

class XPD:
    objlist = []
    def _getuid(self):
        return str(uuid.uuid1())

    def export(self):
        return self.md

    @classmethod
    def _update_objlist(cls,name):
        cls.objlist.append(name)
        return cls.objlist

    def _yaml_path(self):
        os.makedirs(yaml_dir, exist_ok = True)
        return yaml_dir

    def _yaml_garage_path(self):
        yaml_garage_dir_path = os.path.join(self._home_path, 'config_base', 'yml_garage')
        # backup directory when user wants to move out objects from default reading list
        os.makedirs(yaml_garage_dir_path, exist_ok = True)
        return yaml_garage_dir_path

    def _yamify(self):
        '''write a yaml file for this object and place it in config_base/yml'''
        oname = self.name
        ftype = self.type
        cleaned_oname = _clean_name(oname)
        cleaned_ftype = _clean_name(ftype)
        fname = str(cleaned_ftype) +'_'+ str(cleaned_oname) +'.yml'
        XPD._update_objlist(fname)
        fpath = os.path.join(self._yaml_path(), fname)
#        lname = os.path.join(yaml_dir,'_acqobj_list.yml')
#        if os.path.isfile(lname):
#            pass
#        else:
#            obj_list = [fname]
#            yaml.dump(obj_list,lname)
        if isinstance(fpath, str):
            with open(fpath, 'w') as fout:
                yaml.dump(self, fout)
        else:
            yaml.dump(self, fpath)
        return fpath

    @classmethod
    def _get_yaml_list(cls):
        fpath = cls._yaml_path
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
    def __init__(self, pi_last, safn, wavelength, experimenters = [], **kwargs):
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
    if root_dir is None:
        root_dir = glbl.base
    #dp = DataPath(root_dir)
    # remove any existing exports
    if os.path.isdir(glbl.export_dir):
        shutil.rmtree(glbl.export_dir)
    f_name = strftime('data4export_%Y-%m-%dT%H%M')
    os.makedirs(glbl.export_dir, exist_ok=True)
    cur_path = os.getcwd()
    try:
        os.chdir(glbl.base)
        print('Compressing your data now. That may take several minutes, please be patient :)' )
        tar_return = shutil.make_archive(f_name, ar_format, root_dir=glbl.base,
                base_dir='xpdUser', verbose=1, dry_run=False)
        shutil.move(tar_return, glbl.export_dir)
    finally:
        os.chdir(cur_path)
    out_file = os.path.join(glbl.export_dir, os.path.basename(tar_return))
    if not end_beamtime:
        print('New archive file with name '+out_file+' written.')
        print('Please copy this to your local computer or external hard-drive')
    return out_file
    
def _clean_name(name,max_length=25):
    '''strips a string, but also removes internal whitespace
    '''
    if not isinstance(name,str):
        sys.exit(_graceful_exit('Your input, {}, appears not to be a string. Please try again'.format(str(name))))
    cleaned = "".join(name.split())
    if len(cleaned) > max_length:
        sys.exit(_graceful_exit('Please try a name for your object that is < {} characters long'.format(str(max_length))))
    return cleaned

def _clean_md_input(obj):
    ''' strip white space '''
    if isinstance(obj, str):
        return obj.strip()
    elif isinstance(obj, list):
        clean_list = [_clean_md_input(i) for i in obj]
        return clean_list
    elif isinstance(obj, tuple):
        clean_tuple = tuple([_clean_md_input(i) for i in obj])
        return clean_tuple
    # fixme if we need it, but dicts won't be cleaned recursively......
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
