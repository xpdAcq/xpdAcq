import unittest
import os
import shutil
import time
import uuid
#from xpdacq.xpdacq import _areaDET
#from xpdacq.xpdacq import _tempController
#from xpdacq.xpdacq import _shutter
#from xpdacq.xpdacq import _bdir
#from xpdacq.xpdacq import _cdir
#from xpdacq.xpdacq import _hdir
#from xpdacq.xpdacq import _hostname
from xpdacq.glbl import glbl
from xpdacq.xpdacq import _read_dark_yaml, _find_right_dark, _qualified_dark, _qualified_uid, _execute_find_right_dark, _yamify_dark 

class findRightDarkTest(unittest.TestCase): 

    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir,'xpdUser')
        self.dark_dir = os.path.join(self.home_dir, 'dark_base')
        self.D_DIR = [ el for el in glbl.allfolders if el.endswith('dark_base')][0]

        self.PI_name = 'Billinge '
        self.saf_num = 123
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee','S0ham',1),('Terban ',' Max',2)]
        #self.experimenters = [('me ',' you')]

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir,'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir,'xpdConfig'))
   
    def test_read_dark_yaml(self):
        self.assertEqual(self.dark_dir, self.D_DIR)
        os.makedirs(self.dark_dir, exist_ok = True)
        # case 1 : there is no yaml in dark_dir
        self.assertEqual(_read_dark_yaml(5.0), list())
        # case 2: there are more than one dark yamls in dark_dir and one of them is within expire_time
        dark_def_list = []
        for i in range(2):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            f_name = _yamify_dark(dark_def)
            time.sleep(20)
            dark_def_list.append(dark_def)
        self.assertEqual(_read_dark_yaml(0.1), dark_def_list[-len(_read_dark_yaml(0.1)):])
        # case 3: there are more than one dark yamls in dark_dir, but none of them is right one
        dark_def_list = []
        for i in range(3):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            f_name = _yamify_dark(dark_def)
            time.sleep(6)
            dark_def_list.append(dark_def)
        self.assertEqual(_read_dark_yaml(5.0), list())
    
    def test_find_righ_dark(self):
        os.makedirs(self.dark_dir, exist_ok = True)
        # generate dark_pool to play with
        dark_pool = []
        for i in range(1,10):
            dark_def = {str(i*0.1): (str(uuid.uuid1()), time.time())}
            #f_name = _yamify_dark(dark_def)
            dark_pool.append(dark_def)
        print(dark_pool)    
        # case 1: there is a qualified dark in dark_pool given
        for i in range(1,10): # aggresively to test every case
            info_tuple = list(dark_pool[i-1].values())
            for el in info_tuple:
                for sub_el in el:
                    if isinstance(sub_el, str): dark_uid = sub_el
            self.assertEqual(_find_right_dark(dark_pool, i*0.1), dark_uid)
        
        # case 2: no qualified dark in dark pool given
        self.assertEqual(_find_right_dark(dark_pool, 60.0), None) 
