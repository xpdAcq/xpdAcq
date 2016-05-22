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
from collections import OrderedDict
import copy
from xpdacq.glbl import glbl
from xpdacq.utils import _graceful_exit

from bluesky.plans import Plan

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
                #myuid = i._get_obj_uid(i.name,i.type)
                if iter-1 not in hlist:
                    print(i.type+' object '+str(i.name)+' has list index ', iter-1)#'and uid',myuid[:6])
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
    ''' Class that holds basic information to current beamtime 
    
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
    ''' class that holds experiment information 
    
    Parameters
    ----------
    expname : str
        name to this experiment
    
    beamtime : xpdAcq.beamtime.Beamtime object
        object to current beamtime
    
    **kwargs : dict
        optional. a dictionary for user-supplied information.
    ''' 
    def __init__(self, expname, beamtime, **kwargs):
        self.bt = beamtime
        self.name = _clean_md_input(expname)
        self.type = 'ex'
        self.md = self.bt.md
        self.md.update({'ex_name': self.name})
        self.md.update({'ex_uid': self._getuid()})
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
    ''' class that holds sample information 
    
    Parameters
    ----------
    samname : str
        name to this sample
    
    experiment : xpdAcq.beamtime.Experiment object
        object that contains information of experiment
    
    **kwargs : dict
        optional. a dictionary for user-supplied information.
    '''
    def __init__(self, samname, experiment, **kwargs):
        self.name = _clean_md_input(samname)
        self.type = 'sa'
        self.ex = experiment
        self.md = self.ex.md
        self.md.update({'sa_name': self.name})
        self.md.update({'sa_uid': self._getuid()})
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
    '''ScanPlan class  that defines scan plan to run.

    To run it ``prun(Sample,ScanPlan)``

    Parameters
    ----------
    scanoplanname : str
        scanplan name.  Important as new scanplans will overwrite older ones with the same name.

    scan_type : str
        type of scanplan. Currently allowed values are 'ct','tseries', 'Tramp' 
        where  ct=count, tseries=time series (series of counts), and Tramp=Temperature ramp.

    scan_params : dict
        contains all scan parameters that will be passed and used at run-time
        Don't make typos in the dictionary keywords or your scans won't work.
        Entire list of allowed keywords is in the documentation on https://xpdacq.github.io/
        Here is are examples of properly instatiated ScanPlan object:
          * ct_sp = ('<ct name>', 'ct',  {'exposure': <exposure time in S>})
          * tseries_sp = ('<tseries name>', 'tseries', {'exposure':'<exposure time in S>, 'num':<total count>, 'delay':<delay between count in S>})
          * Tramp_sp = ('<Tramp name>', 'Tramp', {'exposure':'<exposure time in S>, 'sartingT':<in K>, 'endinT':<in K>, 'Tstep':<in K>})

    shutter : bool
        default is True. If True, in-hutch fast shutter will be opened before a scan and closed afterwards.
        Otherwise control of the shutter is left external. Set to False if you want to control the shutter by hand.

    livetable : bool
        default is True. It gives LiveTable output when True, not otherwise

    verify_write : bool
        default is False. This verifies that tiff files have been written for each event.
        It introduces a significant overhead so mostly used for testing.
    '''
    def __init__(self, name, scanplan_type = '', scanplan_params = {},
            dk_window = None, shutter=True, **kwargs):
        _ct_required_params = ['exposure']
        _tseries_required_params = ['exposure', 'delay', 'num']
        _Tramp_required_params = ['exposure', 'startingT', 'endingT', 'Tstep']
        # extra efforts to keep print statement in order later
        _ordered_sp_params = _ct_required_params.copy()
        _ordered_sp_params.extend(_tseries_required_params)
        _ordered_sp_params.extend(_Tramp_required_params)
        _sp_params_list = list(OrderedDict.fromkeys(_ordered_sp_params))
        _sp_name = name.strip()
        _control_params = '' # str represents control options.
        if not scanplan_type or not scanplan_params:
            (scanplan_type, scanplan_params) = self._scanplan_name_parser(_sp_name)
        self.type = 'sp'
        self.scanplan = _clean_md_input(scanplan_type)
        self.sp_params = scanplan_params # sp_parms is a dictionary
        self._is_bs = False # priviate attribute
        if 'bluesky_plan' in self.sp_params:
            self._is_bs = True
        self._plan_validator()

        self.shutter = shutter
        self.md = {}

        self.md.update({'sp_params': scanplan_params})
        self.md.update({'sp_type': _clean_md_input(self.scanplan)})
        self.md.update({'sp_usermd':_clean_md_input(kwargs)})
        if self.shutter:
            self.md.update({'sp_shutter_control':'in-scan'})
        else:
            self.md.update({'sp_shutter_control':'external'})
            _control_params += 'nS' # only wirte down non-default behavior

        if not dk_window:
            dk_window = glbl.dk_window
        self.md.update({'sp_dk_window': dk_window})

        # scanplan name should include options in sub_dict, generate it at the last moment
        if _control_params:
            sp_name = '_'.join([_sp_name, _control_params])
        else:
            sp_name = _sp_name
        self.name = sp_name
        self.md.update({'sp_name': _clean_md_input(self.name)})
        print('You have created a "{}" type ScanPlan with name = "{}"'.format(scanplan_type, sp_name))
        print('Corresponding scan parameters are:')
        # extra efforts to keep printing order
        for i in range(len(_sp_params_list)):
            el = _sp_params_list[i]
            try:
                print('{} = {}'.format(el, self.md['sp_params'][el]))
            except KeyError:
                # all errors should be handled before this step
                # except for bluesky plan
                pass
        print('with fast-shutter control = {}'.format(self.shutter))
        fname = self._name_for_obj_yaml_file(self.name,self.type)
        objlist = _get_yaml_list()
        # get objlist from yaml file
        if fname in objlist:
            olduid = self._get_obj_uid(self.name,self.type)
            self.md.update({'sp_uid': olduid})
        else:
            self.md.update({'sp_uid': self._getuid()})
        self._yamify()

    def _scanplan_name_parser(self, sp_name):
        ''' function to parse name of ScanPlan object into parameters fed into ScanPlan

        expected format for each type is following:
        1) 'ct_10' means Count scan with 10s exposure time in total
        2) 'Tramp_10_300_200_5' means temperature ramp from 300k to 200k with 5k step and 10s exposure time each
        3) 'tseries_10_60_5' means time series scan of 10s exposure time each scan 
            and run for 5 scans with 60s delay between them.
        '''
        _ct_required_params = ['exposure']
        _tseries_required_params = ['exposure', 'delay', 'num']
        _Tramp_required_params = ['exposure', 'startingT', 'endingT', 'Tstep']

        _ct_optional_params = ['det','subs_dict']
        _Tramp_optional_params = ['det', 'subs_dict']
        _tseries_optional_params = ['det', 'subs_dict']

        parsed_object = sp_name.split('_') # it will split recursively
        scanplan_type = parsed_object[0]
        # turn parameters into floats
        _sp_params = []
        for i in range(1, len(parsed_object)):
            try:
                _sp_params.append(float(parsed_object[i]))
            except ValueError:
                sys.exit(_graceful_exit('''xpdAcq can not parse your positional argument "{}".
                We use SI units across package, so "5s" or "10k" is not necessary.
                For more information, please go to
                http://xpdacq.github.io.\n'''.format(parsed_object[i])))
                return
        # assgin exposure as it is common parameter
        exposure = _sp_params[0]
        sp_params = {'exposure':exposure}
        if scanplan_type not in glbl._allowed_scanplan_type:
            sys.exit(_graceful_exit('''{} is not a supported ScanPlan type under current version of xpdAcq.
                                    Current supported type are {}.
                                    Please go to http://xpdacq.github.io for more information or request
                                    '''.format(scanplan_type, glbl._allowed_scanplan_type)))
        if scanplan_type == 'ct' and len(_sp_params) == 1: # exposure
            return (scanplan_type, sp_params)
        elif scanplan_type == 'Tramp' and len(_sp_params) == 4: # exposure, startingT, endingT, Tstep
            sp_params.update({'startingT': _sp_params[1], 'endingT': _sp_params[2], 'Tstep': _sp_params[3]})
            return (scanplan_type, sp_params)
        elif scanplan_type == 'tseries' and len(_sp_params) == 3: # exposure, delay, num
            sp_params.update({'delay': _sp_params[1], 'num': int(_sp_params[2])})
            return (scanplan_type, sp_params)
        elif scanplan_type == 'bluesky':
            # leave a hook for future bluesky plan autonaming
            pass
        else:
            sys.exit(_graceful_exit('''xpdAcq can't parse your scanplan name {} into corresponding parameters.
                                    Please do ``ScanPlan?`` to find out currently supported conventions.
                                    or you can define your scanplan parameter dictionary explicitly.
                                    For more information, go to http://xpdacq.github.io
                                    '''.format(sp_name)))

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

        _tseries_required_params = ['exposure', 'delay', 'num']

        if self.scanplan == 'ct':
            for el in _ct_required_params:
                try:
                    self.sp_params[el]
                except KeyError:
                    print('It seems you are using a Count scan but the scan_params dictionary does not contain "{}"which is needed.'.format(el))
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

        elif self.scanplan == 'bluesky':
            print('''INFO: You are handing a "bluesky" type scan.
            Please go to https://nsls-ii.github.io/bluesky/plans.html
            for complete guide on how to define a plan.''')
            print('INFO: This ScanPlan does not support auto-dark subtraction')
        else:
            print('It seems you are defining an unknown scan')
            print('Please use uparrow to edit and retry making your ScanPlan object')
            sys.exit('Please ignore this RunTime error and continue, using the hint above if you like')

class _Union(XPD):
    def __init__(self,sample,scan):
        self.type = 'cmdo'
        self.sc = scan
        self.sa = sample
        self.md = self.sc.md
        self.md.update(self.sa.md)
 #       self._yamify()    # no need to yamify this

class Scan(XPD):
    ''' a scan class that is the joint unit of Sample and ScanPlan objects

    Scan class supports following ways of assigning Sample, ScanPlan objects:
    1) bt.get(<object_index>), eg. Scan(bt.get(2), bt.get(5))
    2) name of acquire object, eg. Scan('my_experiment', 'ct1s')
    3) index to acquire object, eg. Scan(2,5)
    All of above assigning methods can be used in a mix way.

    Parameters:
    -----------
    sample: xpdacq.beamtime.Sample
        instance of Sample class that holds sample related metadata

    scanplan: xpdacq.beamtime.ScanPlan
        instance of ScanPlan calss that hold scanplan related metadata

    '''
    def __init__(self,sample, scanplan):
        self.type = 'sc'
        _sa = self._execute_obj_validator(sample, 'sa', Sample)
        self.sa = _sa
        self.md = dict(self.sa.md)
        _sp = self._execute_obj_validator(scanplan, 'sp', ScanPlan)
        self.sp = _sp
        try:
            sp_md = self.sp.md
        except:
            sp_md = {}
        # create a new dict copy.
        self.md.update(sp_md)

    def _execute_obj_validator(self, input_obj, expect_yml_type, expect_class):
        parsed_obj = self._object_parser(input_obj, expect_yml_type)
        output_obj = self._acq_object_validator(parsed_obj, expect_class)
        return output_obj

    def _object_parser(self, input_obj, expect_yml_type):
        '''a priviate parser for arbitrary object input
        '''
        FEXT = '.yml'
        e_msg_str_type = '''Can't find your "{} object {}". Please do bt.list() to make sure you type right name'''.format(expect_yml_type, input_obj)
        e_msg_ind_type = '''Can't find object with index {}. Please do bt.list() to make sure you type correct index'''.format(input_obj)
        if isinstance(input_obj, str):
            yml_list = _get_yaml_list()
            # note: el.split('_', maxsplit=1) = (yml_type, yml_name)
            yml_name_found = [el for el in yml_list if el.split('_', maxsplit=1)[0] == expect_yml_type
                            and el.split('_', maxsplit=1)[1] == input_obj+FEXT]
            if yml_name_found:
                with open(os.path.join(glbl.yaml_dir, yml_name_found[-1]), 'r') as f_out:
                    output_obj = yaml.load(f_out)
                return output_obj
            else:
                # if still can't find it after going over entire list
                sys.exit(_graceful_exit(e_msg_str_type))
        elif isinstance(input_obj, int):
            try:
                output_obj = self.get(input_obj)
                return output_obj
            except IndexError:
                sys.exit(_graceful_exit(e_msg_ind_type))
        else:
            # let xpdAcq object validator deal with other cases
            return input_obj
    
    def _acq_object_validator(self, input_obj, expect_class):
        ''' filter of object class to Scan
        '''
        if isinstance(input_obj, expect_class):
            return input_obj
        else:
            # necessary. using _graceful_exit will burry useful error message
            # comforting message comes after this TypeError
            raise TypeError('''Incorrect object assignment on {}.
Remember xpdAcq like to think "run this Sample(sa) with this ScanPlan(sp)"
Please do bt.list() to make sure you are handing correct object type'''.format(expect_class))

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
