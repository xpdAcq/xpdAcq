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
import shutil
import datetime
from time import strftime
from xpdacq.config import DataPath


class XPD():
    _base_path = ''
    def _getuid(self):
        return str(uuid.uuid1())

#    def _gohome(self):
#        datapath = DataPath('./')
#        os.chdir(datapath.base)

    def export(self):
        return self.md
        
    def _yaml_path(self):
        if os.path.isdir(os.path.join(self._base_path,'config_base/yml')):
            pass
        elif os.path.isdir(os.path.join(self._base_path,'config_base')):
            os.mkdir(os.path.join(self._base_path,'config_base/yml'))
        else:
            os.mkdir(os.path.join(self._base_path,'config_base'))
            os.mkdir(os.path.join(self._base_path,'config_base/yml'))

        return os.path.join(self._base_path,'config_base/yml')

    def _yamify(self):
        fname = self.name
        ftype = self.type
        fpath = os.path.join(self._yaml_path(),ftype+'_'+fname+'.yml')
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

class Beamtime(XPD):
    def __init__(self, pi_last, safn):
        self.name = 'bt'
        self.type = 'bt'
        self.md = {'bt_piLast': pi_last, 'bt_safN': safn}
        self.md.update({'bt_uid': self._getuid()})
        self._yamify()

class Experiment(XPD):
    def __init__(self, expname, beamtime):
        self.name = expname
        self.type = 'ex'
        self.bt = beamtime
        self.md = self.bt.md
        self.md.update({'ex_name': expname})
        self.md.update({'ex_uid': self._getuid()})
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
