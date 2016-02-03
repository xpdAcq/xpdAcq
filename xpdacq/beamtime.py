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
import uuid
import yaml
import os

from xpdacq.config import DataPath

def test():
    dir = {'thing1':{'this':'that','the':'other'},'thing2':{'py':'thon'}}
    
class XPD():
    def _getuid(self):
        return str(uuid.uuid1())
    
#    def _gohome(self):
#        datapath = DataPath('./')
#        os.chdir(datapath.base)
      
    def export(self):
        return self.md
        
    @staticmethod
    def _yaml_path():
        if os.path.isdir('./config_base/yml'):
            pass
        elif os.path.isdir('./config_base'):
            os.mkdir('./config_base/yml')
        else:
            os.mkdir('./config_base/')
            os.mkdir('./config_base/yml')
    
        return './config_base/yml/'

    def _yamify(self):
        fname = self.name
        ftype = self.type
        fpath = self._yaml_path()+ftype+'_'+fname+'.yml'
        if isinstance(fpath, str):
            with open(fpath, 'w') as fout:
                yaml.dump(self, fout )
        else:
            yaml.dump(self, fpath )
            

    def _get_ymls(self):
        fpath = self._yaml_path()
        yamls = os.listdir(fpath)
        return yamls
    
    @classmethod            
    def loadyamls(cls):
        fpath = cls._yaml_path()
        yamls = os.listdir(fpath)
        olist = []
        for f in yamls: 
            fname = fpath+f
            with open(fname, 'r') as fout:
                olist.append(yaml.load(fout))
        return olist
          
    @classmethod
    def list(cls,type=None):
        list = cls.loadyamls()
        if type == None:
            iter = 0
            for i in list:
                iter += 1
                print(i.type+' object '+i.name+' has list index ',iter-1)
        else:    
            iter = 0
            for i in list:
                iter += 1
                if i.type == type:
                    print(i.type+' object '+i.name+' has list index ',iter-1)
        print('Use bt.get(index) to get the one you want')

    @classmethod
    def get(cls,index):
        list = cls.loadyamls()
        return list[index]

class Beamtime(XPD):
    def __init__(self, pi_last, safn):
        self.name = 'bt'
        self.type = 'bt'
        self.md = {'bt_piLast': pi_last, 'bt_safN':safn}
        self.md.update({'bt_uid': self._getuid()})
        self._yamify()    

class Experiment(XPD):
    def __init__(self, expname, beamtime):
        self.name = expname
        self.type = 'ex'
        self.bt = beamtime
        self.md = self.bt.md
        self.md.update({'ex_name':expname})
        self.md.update({'ex_uid': self._getuid()})
        self._yamify()    
        
class Sample(XPD):
    def __init__(self, samname, experiment):
        self.name = samname
        self.type = 'sa'
        self.ex = experiment
        self.md = self.ex.md
        self.md.update({'sa_name': samname})
        self.md.update({'sa_uid': self._getuid()})
        self._yamify()    
      
    
class Scan(XPD):
    def __init__(self,scanname,sample):
        self.name = scanname
        self.type = 'sc' 
        self.sa = sample
        self.md = self.sa.md
        self.md.update({'sc_name': scanname})
        self.md.update({'sc_uid': self._getuid()})
        self._yamify()    
        #self.test1 = 'test'
        #self.test2 = 123 


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
