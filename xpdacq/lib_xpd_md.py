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

## library of xpd_md class

def _timestampstr(timestamp):
    import datetime
    time = str(datetime.datetime.fromtimestamp(timestamp))
    date = time[:10]
    hour = time[11:16]
    m_hour = hour.replace(':','-')
    timestampstring = '_'.join([date,hour])
    #corrected_timestampstring = timestampstring.replace(':','-')
    return timestampstring

def _get_namespace(var_name):
    ''' this function get and varify if a variable exits in current ipython shell
        mainly used to check valied motor name
    '''
    ipshell = get_ipython()
    try:
        var_val = ipshell.user_ns[var_name]
    except KeyError:
        print('%s does not exit in current name space. Please check if it is instaciated' % var_name)
        return
 
    return var_val

def set_beamtime(safN, experimenters, update):
    ''' This function sets up experimenter name(s). This function can be run at anytime to change experimenter global setting
    Argument:
        experimenters - str or list - name of current experimenters
        update - bool - optional. set True to update experimenters list and set False to extend experimenters list
    '''
    print('If you have preloaded this information in a user-config file,')
    print('please place that in the Import directory and run import_config()')
    piLast = input('Please enter the last name of the PI on the SAF (type x to exit):')
    if piLast == 'x': return
        
    #from xpdacq.lib_xpd_md import set_beamtime as st_beamtime
    #out = st_beamtime(safN_val, experimenters_val, update)
    #self.safN = out[0]
    #self.experimenters = out[1]
    #self.modified_time = out[2]
    import time
    experimenters_list = []
    if not isinstance(experimenters, list):
        if isinstance(experimenters, str):
            experimenters_list.append(experimenters)
        else:
            raise TypeError('Experimenters needs to be str or list')
    else:
        experimenters_list = experimenters

    if not isinstance(safN, str):
        raise TypeError('SAF number needs to be a str')
    
    timestamp = _timestampstr(time.time())    
    print('Current experimenters is/are %s' % experimenters_list)
    print('Current SAF number is %s' % safN)

    return (safN, experimenters_list, timestamp)


def set_experiment():
    return
    ''' This function sets up experimenter name(s). This function can be run at anytime to change experimenter global setting
    Argument:
        experimenters - str or list - name of current experimenters
        update - bool - optional. set True to update experimenters list and set False to extend experimenters list
    
    experimenters_list = []
    if not isinstance(experimenters, list):
        if isinstance(experimenters, str):
            experimenters_list.append(experimenters)
        else:
            raise TypeError('Experimenters needs to be str or list')
    else:
        experimenters_list = experimenters

    if not isinstance(safN, str):
        raise TypeError('SAF number needs to be a str')
    
    timestamp = _timestampstr(time)    
    print('Current experimenters is/are %s' % experimenters_list)
    print('Current SAF number is %s' % safN)

    return (safN, experimenters_list, timestamp)
    '''

def composition_dict_gen(sample):
    '''generate composition dictionary with desired form

    argument:
    sample_name - tuple - if it is a mixture, give a tuple following corresponding amounts. For example, ('NaCl',1,'Al2O3',2)
    '''

    from xpdacq.utils import composition_analysis
    sample_list = [ el for el in sample if isinstance(el,str)]
    amount_list = [ amt for amt in sample if isinstance(amt, float) or isinstance(amt, int)]
    compo_dict_list = []
    for i in range(len(sample_list)):
        compo_dict = {}
        compo_dict['phase_name'] = sample_list[i]
        compo_analysis_dict = {}
        (e,a) = composition_analysis(sample_list[i])
        for j in range(len(e)):
            compo_analysis_dict[e[j]] = a[j]
        compo_dict['element_info'] = compo_analysis_dict
        compo_dict['phase_amount'] = amount_list[i]
        
        compo_dict_list.append(compo_dict)
    return compo_dict_list


def set_sample(sample_name, sample, time):
    '''set up metadata fields for your runengine

    This function sets up persistent metadata that will be saved with subsequent scans,
    including a list of experimenters and the sample composition, as well as other user
    defined comments.  It can be rerun multiple times until you are happy with the settings,
    then these settings will be applied to scan metadata when the scans are run later.

    Arguments:
    
    sample_name - str - name to your sample
    sample - tuple- a tuple including sample name such as "dppa2" or "Al2O3" and corresponding amount.
        For example, ('CaCO3',1.0) means a pure sample and ('CaCO3',1.0,'TiO2',2.0) stands for a 1:2 mix of CaCO3 and TiO2
    '''
    #gs = _bluesky_global_state()

    if not isinstance(sample_name, str):
        raise TypeError('sample_name must be a str')
    
    if not isinstance(sample, tuple):
        raise TypeError('sample must be a tuple in order to generate composition dictionary')

    composition = composition_dict_gen(sample)
    timestamp = _timestampstr(time)
    print('Current sample_name is %s' % sample_name)
    print('Current composition is %s' % composition)
 
    return (sample_name, composition, timestamp) 


def set_scan():
    return

def set_event():
    return

def show_obj(obj):
    full_info = obj.__dict__
    real_info = {}
    
    for k in full_info.keys():
        if k.islower():
            real_info[k] = full_info.get(k)

    print(full_info)
    
    return real_info
   

###########################################################


