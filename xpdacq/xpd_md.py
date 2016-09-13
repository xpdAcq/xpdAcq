##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################

## xpd md data, using composition method

import time

## current logic: this metadata class manage data input, lib_xpd_md takes care of method

class Beamtime(object):
    def __init__(self, safN, start_date, end_date, experimenters = [], update = False ):
        import uuid
        uid = str(uuid.uuid1())
        self.beamtime_uid = uid
        print('uid to this beamtime is %s' % uid)

        self.beamtime_start_date = start_date
        self.beamtime_end_date = end_date
        print('start date and end date of this beamtime: ( %s, %s )' % (start_date, end_date))
       
        self.modified_time = time.time() 
        
        self.set_beamtime(safN, experimenters, update)

    def set_beamtime(self, safN_val, experimenters_val, update = False):
        pass

    def show_beamtime(self):
        full_info = self.__dict__
        real_info = {}
        for k in full_info.keys():
            if k.islower():
                real_info[k] = full_info.get(k)
        return real_info


class Experiment(object):
    def __init__(self, obj, user_dict=None, env_var=None):
        import uuid
        from xpdacq.lib_xpd_md import _get_namespace

        uid = str(uuid.uuid1())
        self.experiment_uid = uid
       
        # dump user supplied info into class 
        if user_dict:
            for k,v in user_dict.items():
                setattr(self, k, v)  
            self.set_experiment()

        self.Beamtime = obj
        
        # hook to environment variable
        if env_var:
            env_dict = {}
            if isinstance(env_var, str):
                env_var_op = []
                env_var_op.append(env_var)
            elif isinstance(env_var, list):
                env_var_op = env_var
            else:
                print('motor/detector name should be a string or a list')
                return
            for el in env_var_op:
                env_dict[el] = _get_namespace(el)
            env_key = env_dict.keys()
            env_val = env_dict.values()
            print('Your have included environment varibales and its corresponding values: %s' % env_dict)

    def set_experiment(self):
        from xpdacq.lib_xpd_md import set_experiment
        out = set_experiment() # remain as a method but it does nothing now

    def show_experiment(self):
        full_info = self.__dict__
        real_info = {}
        for k in full_info.keys():
            if k.islower():
                real_info[k] = full_info.get(k)
        return real_info
    
    def __getattr__(self, name):
        # get attributes from all parent layer
        return getattr(self.Beamtime, name)
        
class Sample(object):
    def __init__(self, obj, sample_name='', composition=(), comments='', time = time.time()):
        import uuid
        uid = str(uuid.uuid1())
        self.sample_uid = uid

        self.set_sample(sample_name, composition)
        self.sample_comments = comments

        # assign Experiment to object name
        self.Experiment = obj

    def set_sample(self, sample_name_val, sample_val, time = time.time()):
        ''' 
        Set up data in sample object
        
        Arguments:
            sample_name_val - str - sample name, like 'NaCl' or 'NADDPH'
            sample_val - tuple - tuple that represents chemical composition. For example: ('Na', 1, 'Cl', 1)
        '''
        from xpdacq.lib_xpd_md import set_sample
        out = set_sample(sample_name_val, sample_val, time)
        self.sample_name = out[0]
        self.composition = out[1]
        self.modified_time = out[2]

    def show_sample(self):
        full_info = self.__dict__
        real_info = {}
        for k in full_info.keys():
            if k.islower():
                real_info[k] = full_info.get(k)
        return real_info

    def __getattr__(self, name):
        # get attributes from all parent layer
        return getattr(self.Experiment, name)


class Scan(object):
    # blusesky has saved most of necessary metadata
    # so I keep method in Scan and Event simple
    def __init__(self, obj, production=True):
        if production:
            # default behavior is not dryrun
            self.scan_tag = 'Production'
        else:
            self.scan_tag = 'Test'
 
        self.Sample = obj

    def set_scan(self, scan_tag):
        from xpdacq.lib_xpd_md import set_scan
        # dummy method
        set_scan()    

    def show_scan(self):
        from xpdacq.lib_xpd_md import show_obj
        out = show_obj(self) 

    def __getattr__(self, name):
        # get attributes from all parent layer
        return getattr(self.Sample, name)


class Event(object):
    # blusesky has saved most of necessary metadata
    # so I keep method in Scan and Event simple
    def __init__(self, obj, production = True):
        if production:
            self.event_tag = 'Production'
        else:
            self.event_tag = 'Test'

        self.Scan = obj 

    def set_event(self):
        from xpdacq.lib_xpd_md import set_scan
        set_scan()

    def show_event(self):
        from xpdacq.lib_xpd_md import show_obj
        out = show_obj(self)
    
    def __getattr__(self, name):
        return getattr(self.Scan, name)
