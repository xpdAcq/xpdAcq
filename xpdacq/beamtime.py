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

def _get_yaml_list():
    yaml_dir = glbl.yaml_dir
    lname = os.path.join(yaml_dir,'_acqobj_list.yml')
    with open(lname, 'r') as fout:
        yaml_list = yaml.load(fout) 
    return list(yaml_list)

def _get_hidden_list():
    yaml_dir = glbl.yaml_dir
    lname = os.path.join(yaml_dir,'_hidden_objects_list.yml')
    with open(lname, 'r') as fout:
        hidden_list = yaml.load(fout) 
    return list(hidden_list)

def _update_objlist(objlist,name):
    # check whether this obj exists already if yes, don't add it again.
    if name not in objlist:
        objlist.append(name)
    return objlist

class XPD:
    objlist = []
    def _getuid(self):
        return str(uuid.uuid4())

    def export(self):
        return self.md

    def _get_obj_uid(self,name,otype):
        yamls = self.loadyamls()
        uidid = "_".join([otype,'uid'])
        for i in yamls:
            if i.name == name:
                if i.type == otype:
                    ouid = i.md[str(uidid)]
        return ouid

    def _yaml_path(self):
        os.makedirs(yaml_dir, exist_ok = True)
        return yaml_dir

    def _name_for_obj_yaml_file(self,oname,ftype):
        cleaned_oname = _clean_name(oname)
        cleaned_ftype = _clean_name(ftype)
        fname = str(cleaned_ftype) +'_'+ str(cleaned_oname) +'.yml'
        return fname

    def _yamify(self):
        '''write a yaml file for this object and place it in config_base/yml'''
        yaml_dir = glbl.yaml_dir
        lname = os.path.join(yaml_dir,'_acqobj_list.yml')
        oname = self.name
        ftype = self.type
        fname = self._name_for_obj_yaml_file(oname,ftype)
        fpath = os.path.join(self._yaml_path(), fname)
        objlist = _get_yaml_list()
        objlist = _update_objlist(objlist, fname)
        with open(lname, 'w') as fout:
            yaml.dump(objlist, fout)

        if isinstance(fpath, str):
            with open(fpath, 'w') as fout:
                yaml.dump(self, fout)
        else:
            yaml.dump(self, fpath)
        return fpath

    def loadyamls(self):
        yaml_dir = glbl.yaml_dir
        yaml_list = _get_yaml_list()
        olist = []
        for f in yaml_list:
            fname = os.path.join(yaml_dir,f)
            with open(fname, 'r') as fout:
                olist.append(yaml.load(fout))
        return olist

    @classmethod
    def list(cls, type=None):
        olist = cls.loadyamls(cls)
        hlist = _get_hidden_list()
        if type is None:
            iter = 0
            for i in olist:
                iter += 1
                myuid = i._get_obj_uid(i.name,i.type)
                if iter-1 not in hlist:
                    print(i.type+' object '+str(i.name)+' has list index ', iter-1,'and uid',myuid[:6])
        else:
            iter = 0
            for i in olist:
                iter += 1
                if i.type == type:
                    if iter-1 not in hlist:
                        print(i.type+' object '+str(i.name)+' has list index ', iter-1)
        print('Use bt.get(index) to get the one you want')

    def hide(self,index):
        hidden_list = _get_hidden_list()
        hidden_list.append(index)
        yaml_dir = glbl.yaml_dir
        hname = os.path.join(yaml_dir,'_hidden_objects_list.yml')
        fo = open(hname, 'w')
        yaml.dump(hidden_list, fo)
        return hidden_list

    def unhide(self,index):
        hidden_list = _get_hidden_list()
        while index in hidden_list: 
            hidden_list.remove(index)
        yaml_dir = glbl.yaml_dir
        hname = os.path.join(yaml_dir,'_hidden_objects_list.yml')
        fo = open(hname, 'w')
        yaml.dump(hidden_list, fo)
        return hidden_list

    # test at XPD
    def _init_dark_scan_list(self):
        dark_scan_list = []
        with open(glbl.dk_yaml,'w') as f:
            yaml.dump(dark_scan_list, f)

    @classmethod
    def get(cls, index):
        list = cls.loadyamls(cls)
        return list[index]
    
    def set_wavelength(self,wavelength):
        self.md.update({'bt_wavelength': _clean_md_input(wavelength)})
        self._yamify()

class Beamtime(XPD):
    ''' beamtime object that holds basic information to current beamtime 
    
    Parameters
    ----------
    pi_last : str
        last name of PI to this beamtime
    safn : str
        SAF number to this beamtime
    wavelength : float
        optional but it is strongly recommended to enter. x-ray wavelength to this beamtime, it will be used during data deduction
    experimenters : list
        optional. a list of tuples that are made of (last_name, first_name, id) of each experimenter involved.
    **kwargs : dict
        optional. a dictionary for user-supplied information.
    ''' 
    def __init__(self, pi_last, safn, wavelength=None, experimenters=[], **kwargs):
        self.name = 'bt'
        self.type = 'bt'
        self.md = {'bt_piLast': _clean_md_input(pi_last), 'bt_safN': _clean_md_input(safn), 
                    'bt_usermd':_clean_md_input(kwargs)}
        self.md.update({'bt_wavelength': _clean_md_input(wavelength)})
        self.md.update({'bt_experimenters': _clean_md_input(experimenters)})

        #initialize the objlist yaml file if it doesn't exist
        yaml_dir = glbl.yaml_dir
        lname = os.path.join(yaml_dir,'_acqobj_list.yml')
        hname = os.path.join(yaml_dir,'_hidden_objects_list.yml')
        dname = os.path.join(yaml_dir,'_dk_objects_list.yml')
        if not os.path.isfile(lname):
            objlist = []
            fo = open(lname, 'w')
            yaml.dump(objlist, fo)
        if not os.path.isfile(hname):
            hidlist = []
            fo = open(hname, 'w')
            yaml.dump(hidlist, fo)
        if not os.path.isfile(dname):
            dklist = []
            fo = open(dname, 'w')
            yaml.dump(dklist, fo)
   
        fname = self._name_for_obj_yaml_file(self.name,self.type)
        objlist = _get_yaml_list()
        # get objlist from yaml file
        if fname in objlist:
            olduid = self._get_obj_uid(self.name,self.type)
            self.md.update({'bt_uid': olduid})
        else:
            self.md.update({'bt_uid': self._getuid()})
        self._yamify()

class Experiment(XPD):
    def __init__(self, expname, beamtime, **kwargs):
        self.bt = beamtime
        self.name = _clean_md_input(expname)
        self.type = 'ex'
        self.md = self.bt.md
        self.md.update({'ex_name': self.name})
#        self.md.update({'ex_uid': self._getuid()})
        self.md.update({'ex_usermd':_clean_md_input(kwargs)})
        fname = self._name_for_obj_yaml_file(self.name,self.type)
        objlist = _get_yaml_list()
        # get objlist from yaml file
        if fname in objlist:
            olduid = self._get_obj_uid(self.name,self.type)
            self.md.update({'ex_uid': olduid})
        else:
            self.md.update({'ex_uid': self._getuid()})
        self._yamify()

class Sample(XPD):
    def __init__(self, samname, experiment, **kwargs):
        self.name = _clean_md_input(samname)
        self.type = 'sa'
        self.ex = experiment
        self.md = self.ex.md
        self.md.update({'sa_name': self.name})
#        self.md.update({'sa_uid': self._getuid()})
        self.md.update({'sa_usermd': _clean_md_input(kwargs)})
        fname = self._name_for_obj_yaml_file(self.name,self.type)
        objlist = _get_yaml_list()
        # get objlist from yaml file
        if fname in objlist:
            olduid = self._get_obj_uid(self.name,self.type)
            self.md.update({'sa_uid': olduid})
        else:
            self.md.update({'sa_uid': self._getuid()})
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
    def __init__(self,name, scanplan_type, scanplan_params, shutter=True, livetable=True, verify_write=False, **kwargs):
        self.name = _clean_md_input(name)
        self.type = 'sp'
        self.scanplan = _clean_md_input(scanplan_type)
        self.sp_params = scanplan_params # sc_parms is a dictionary
        
        self._plan_validator()
        
        self.shutter = shutter
        self.md = {}
        self.md.update({'sp_name': _clean_md_input(self.name)})
        self.md.update({'sp_type': _clean_md_input(self.scanplan)})
        self.md.update({'sp_usermd':_clean_md_input(kwargs)})
        if self.shutter: 
            self.md.update({'sp_shutter_control':'in-scan'})
        else:
            self.md.update({'sp_shutter_control':'external'})
        
        subs=[]
        if livetable:
            subs.append('livetable')
        if verify_write:
            subs.append('verify_write')
        if len(subs) > 0:
            scanplan_params.update({'subs':_clean_md_input(subs)}) 
        self.md.update({'sp_params': _clean_md_input(scanplan_params)})
        fname = self._name_for_obj_yaml_file(self.name,self.type)
        objlist = _get_yaml_list()
        # get objlist from yaml file
        if fname in objlist:
            olduid = self._get_obj_uid(self.name,self.type)
            self.md.update({'sp_uid': olduid})
        else:
            self.md.update({'sp_uid': self._getuid()})
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
        _Tramp_required_params = ['startingT', 'endingT', 'Tstep', 'exposure']
        _Tramp_optional_params = ['det', 'subs_dict']

        _ct_required_params = ['exposure']
        _ct_optional_params = ['det','subs_dict'] 
        # leave optional parameter list here, in case we need to use them in the future
        
        
        # params in tseries is not completely finalized
        _tseries_required_params = ['exposure', 'delay', 'num']
        
        if self.scanplan == 'ct':
            for el in _ct_required_params:
                try:
                    self.sp_params[el]
                except KeyError:
                    print('It seems you are using a Count scan but the scan_params dictionary does not contain {}  which is needed.'.format(el))
                    print('Please use uparrow to edit and retry making your ScanPlan object')
                    sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')

        elif self.scanplan == 'Tramp':
            for el in _Tramp_required_params:
                try:
                   self.sp_params[el]
                except KeyError:
                   print('It seems you are using a temperature ramp scan but the scan_params dictionary does not contain {} which is needed.'.format(el))
                   print('Please use uparrow to edit and retry making your ScanPlan object')
                   sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')
        
        elif self.scanplan == 'tseries':
           for el in _tseries_required_params:
               try:
                   self.sp_params[el]
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

class Scan(XPD):
    ''' a scan class that is the joint unit of Sample and ScanPlan objects'''
    def __init__(self,sample, scanplan):
        self.type = 'sc'
        self.sp = scanplan
        self.sa = sample
        self.md = dict(self.sp.md) # create a new dict copy.
        self.md.update(self.sa.md)

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
