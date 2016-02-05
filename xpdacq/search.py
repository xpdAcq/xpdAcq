import os
import time
import copy
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import json

import bluesky
from bluesky.scans import *
from bluesky.broker_callbacks import LiveImage
from bluesky.callbacks import CallbackBase, LiveTable, LivePlot

from ophyd.commands import *
from ophyd.controls import *

from dataportal import DataBroker as db
from dataportal import get_events, get_table, get_images
from metadatastore.commands import find_run_starts

from xpdacquire.config import datapath
from xpdacquire.utils import composition_analysis
from tifffile import *


pd.set_option('max_colwidth',40)
pd.set_option('colheader_justify','left')

default_keys = ['owner', 'beamline_id', 'group', 'config', 'scan_id'] # required by dataBroker
feature_keys = ['sample_name','experimenters'] # required by XPD, time_stub and uid will be automatically added up as well

# These are the default directory paths on the XPD data acquisition computer.  Change if needed here
W_DIR = datapath.tif                # where the user-requested tif's go.  Local drive
R_DIR = datapath.config             # where the xPDFsuite generated config files go.  Local drive
D_DIR = datapath.dark               # where the tifs from dark-field collections go. Local drive
S_DIR = datapath.script             # where the user scripts go. Local drive

# Instanciate bluesky objects

def _bluesky_RE():
    import bluesky
    from bluesky.run_engine import RunEngine
    from bluesky.run_engine import DocumentNames
    RE = RunEngine()
    bluesky.register_mds.register_mds(RE)
    return RE

'''def _bluesky_metadata_store():
    Return the dictionary of bluesky global metadata.
    
    gs = _bluesky_global_state()
    return gs.RE.md
'''

ipshell = get_ipython()
gs = ipshell.user_ns['gs']
RE = _bluesky_RE()
pe1 = ipshell.user_ns['pe1']
cs700 = ipshell.user_ns['cs700']
sh1 = ipshell.user_ns['sh1']
gs.TEMP_CONTROLLER = cs700
tth_cal = ipshell.user_ns['tth_cal']
th_cal = ipshell.user_ns['th_cal']
photon_shutter = ipshell.user_ns['photon_shutter']

def feature_gen(header):
    ''' generate a human readable file name. It is made of time + uid + sample_name + user

    field will be skipped if it doesn't exist
    '''
    uid = header.start.uid
    time_stub = _timestampstr(header.start.time)

    dummy_list = []
    for key in feature_keys:
        try:
            # truncate length
            if len(header.start[key])>12:
                value = header.start[key][:12]
            else:
                value = header.start[key]
            # clear space
            dummy = [ ch for ch in list(value) if ch!=' ']
            dummy_list.append(''.join(dummy))  # feature list elements is at the first level, as it should be
        except KeyError:
            pass

    inter_list = []
    for el in dummy_list:
        if isinstance(el, list): # if element is a list
            join_list = "_".join(el)
            inter_list.append(join_list)
        else:
            inter_list.append(el)
    feature = "_".join(inter_list)
    return feature

def _timestampstr(timestamp):
    time = str(datetime.datetime.fromtimestamp(timestamp))
    date = time[:10]
    hour = time[11:16]
    m_hour = hour.replace(':','-')
    timestampstring = '_'.join([date,hour])
    #corrected_timestampstring = timestampstring.replace(':','-')
    return timestampstring

def _MD_template():
    ''' use to generate idealized metadata structure, for pictorial memory and
    also for data cleaning.
    '''
    #gs = _bluesky_global_state()
    _clean_metadata()
    gs.RE.md['iscalib'] = 0
    gs.RE.md['isdark'] = 0
    gs.RE.md['isbackground'] = 0 # back ground image
    gs.RE.md['experimenters'] = []
    gs.RE.md['sample_name'] = ''
    gs.RE.md['calibrant'] = '' # transient, only for calibration set
    gs.RE.md['user_supply'] = {}
    gs.RE.md['commenets'] = ''
    gs.RE.md['SAF_number'] = ''

    gs.RE.md['sample'] = {}
    gs.RE.md['sample']['composition'] = {}

    gs.RE.md['dark_scan_info'] = {}
    gs.RE.md['scan_info'] = {}

    gs.RE.md['calibration_scan_info'] = {}
    gs.RE.md['calibration_scan_info']['calibration_information'] = {}

    return gs.RE.md

def scan_info():
    ''' hard coded scan information. Aiming for our standardized metadata
    dictionary'''
    #gs = _bluesky_global_state()
    all_scan_info = []
    try:
        all_scan_info.append(gs.RE.md['scan_info']['scan_exposure_time'])
    except KeyError:
        all_scan_info.append('')
    try:
        all_scan_info.append(gs.RE.md['calibration_scan_info']['calibration_scan_exposure_time'])
    except KeyError:
        all_scan_info.append('')
    try:
        all_scan_info.append(gs.RE.md['dark_scan_info']['dark_scan_exposure_time'])
    except KeyError:
        all_scan_info.append('')
    print('scan exposure time is %s, calibration exposure time is %s, dark scan exposure time is %s' % (all_scan_info[0], all_scan_info[1], all_scan_info[2]))


def write_config(d, config_f_name):
    '''reproduce information stored in config file and save it as a config file

    argument:
    d - dict - a dictionary that stores config data
    f_name - str - name of your config_file, usually is 'config+tif_file_name.cfg'
    '''
    # temporarily solution, need a more robust one later on
    import configparser
    config = configparser.ConfigParser()
    for k,v in _dig_dict(d).items():
        config[k] = {}
        config[k] = v # temporarily use
    with open(config_f_name+'.cfg', 'w') as configfile:
        config.write(configfile)

def filename_gen(header):
    '''generate a file name of tif file. It contains time_stub, uid and feature
    of your header'''

    uid = header.start.uid[:5]
    try:
        time_stub = _timestampstr(header.start.time)
    except KeyError:
        tim_stub = 'Imcomplete_Scan'
    feature = feature_gen(header)
    file_name = '_'.join([time_stub, uid, feature])
    return file_name



def run_script(script_name):
    ''' Run user script in script base

    argument:
    script_name - str - name of script user wants to run. It must be sit under script_base to avoid confusion when asking Python to run script.
    '''
    module = script_name
    m_name = os.path.join('S_DIR', module)
    #%run -i $m_name

##### common functions #####


def table_gen(headers):
    ''' Takes in a header list generated by search functions and return a table
    with metadata information

    Argument:
    headers - list - a list of bluesky header objects

    '''
    plt_list = list()
    feature_list = list()
    comment_list = list()
    uid_list = list()

    if type(list(headers)[0]) == str:
        header_list = []
        header_list.append(headers)
    else:
        header_list = headers

    for header in header_list:
        #feature = _feature_gen(header)
        #time_stub = _timestampstr(header.stop.time)
        #header_uid = header.start.uid
        #uid_list.append(header_uid[:5])
        #f_name = "_".join([time_stub, feature])
        f_name =filename_gen(header)
        feature_list.append(f_name)

        try:
            comment_list.append(header.start['comments'])
        except KeyError:
            comment_list.append('None')
        try:
            uid_list.append(header.start['uid'][:5])
        except KeyError:
            # jsut in case, it should never happen
            print('Some of your data do not even have a uid, it is very dangerous, please contact beamline scientist immediately')
    plt_list = [feature_list, comment_list] # u_id for ultimate search
    inter_tab = pd.DataFrame(plt_list)
    tab = inter_tab.transpose()
    tab.columns=['Features', 'Comments' ]

    return tab


def time_search(startTime,stopTime=False,exp_day1=False,exp_day2=False):
    '''return list of experiments run in the interval startTime to stopTime

    this function will return a set of events from dataBroker that happened
    between startTime and stopTime on exp_day

    arguments:
    startTime - datetime time object or string or integer - time a the beginning of the
                period that you want to pull data from.  The format could be an integer
                between 0 and 24 to set it at a  whole hour, or a datetime object to do
                it more precisely, e.g., datetime.datetime(13,17,53) for 53 seconds after
                1:17 pm, or a string in the time form, e.g., '13:17:53' in the example above
    stopTime -  datetime object or string or integer - as starTime but the latest time
                that you want to pull data from
    exp_day - str or datetime.date object - the day of the experiment.
    '''
    # date part
    if exp_day1:
        if exp_day2:
            d0 = exp_day1
            d1 = exp_day2
        else:
            d0 = exp_day1
            d1 = d0
    else:
        d0 = datetime.datetime.today().date()
        d1 = d0

    # time part
    if stopTime:

        t0 = datetime.time(startTime)
        t1 = datetime.time(stopTime)

    else:
        now = datetime.datetime.now()
        hr = now.hour
        minu = now.minute
        sec = now.second
        stopTime = datetime.time(hr,minu,sec) # if stopTime is not specified, set current time as stopTime

        t0 = datetime.time(startTime)
        t1 = stopTime

    timeHead = str(d0)+' '+str(t0)
    timeTail = str(d1)+' '+str(t1)

    header_time=db(start_time=timeHead,
                   stop_time=timeTail)

    event_time = get_events(header_time, fill=False)
    event_time = list(event_time)

    print('||You assign a time search in the period:\n'+str(timeHead)+' and '+str(timeTail)+'||' )
    print('||Your search gives out '+str(len(header_time))+' results||')

    return header_time


#### block of search functions ####
def _list_keys( d, container):
    ''' list out all keys in dictionary, d
    Argument:
        d - dict - input dictionary
        containter - list - auxiliary list
    '''
    if isinstance(d, dict):
        # append keys in the first layer
        container += d.keys()
        # add keys in next layer
        list(map(lambda x: _list_keys(x, container), d.values()))
    elif isinstance(d, list):
        list(map(lambda x: _list_keys(x, container), d))
    


def get_keys(fuzzy_key, d=None, verbose=0):
    ''' fuzzy search on key names contained in a nested dictionary.
    Return all possible key names starting with fuzzy_key:
    Arguments:

    fuzzy_key - str - possible key name, can be fuzzy like 'exp', 'sca' or nearly complete like 'experiment'
    d        -- dictionary you want to search.  Use bluesky metadata store
                when not specified.
    '''
    if d is None:
        #d = _bluesky_metadata_store()
        d = gs.RE.md

    container = []
    _list_keys(d, container)
    
    if verbose:
        # default is not verbose
        print('All keys in target dictionary are: %s' % str(container))
    
    # filter out desired name
    out = list(filter(lambda x: x.startswtih(fuzzy_key), container))
        # just a practice. It is equivalent to out = [ x for x in container if x.startswith(fuzzy_key)]
    return out

def get_keychain(wanted_key, d=None):
    ''' Return keychian(s) of specific key(s) in a nested dictionary

    argumets:
    wanted_key - str - name of key you want to search for
    d        -- dictionary you want to search.  Use bluesky metadata store
                when not specified.
    '''
    if d is None:
        #d = _bluesky_metadata_store()
        d = gs.RE.md
    for k, v in d.items():
        if isinstance(v, dict):
            result = get_keychain(wanted_key, v) # dig in nested element
            if result:
                return [k]+ result
        elif k == wanted_key:
            return [k]

def set_value(key, new_value, d):
    ''' update value of corresponding key in a nested dictionary
    
    argumet:
    key - str - key you want to change
    new_value - str - value of key to-be-updated
    d - dict - target dictionary
    '''
    cur = d
    keychain = get_keychain(key, d)
    key_oper = keychain[-1]
    for path_item in keychain[:-1]:
        try:
            cur = cur[path_item]
        except KeyError:
            cur = cur[path_item] = {}

    old_value = cur[keychain[-1]]
    cur[keychain[-1]] = new_value
    print('Values to key %s has been updated from %s to %s' %(key, old_value, new_value))
    print(d)


def build_keychain_list(key_list, d=None, verbose = 1):
    ''' Return a keychain list that yields all parent keys for every key in key_list
        E.g. d = {'layer1':{'layer2':{'mykey':'value'}}}
            build_keychain_list([layer2, mykey],d) = ['layer1', 'layer1.layer2']
    argumets:
    key_list - str or list - name of key(s) you want to search for
    d        -- dictionary you want to search.  Use bluesky metadata store
                when not specified.
    '''
    if d is None:
        #d = _bluesky_metadata_store()
        d = gs.RE.md
    result = []
    if isinstance(key_list, str):
        key_list_operate = []
        key_list_operate.append(key_list)
    elif isinstance(key_list, list):
        key_list_operate = key_list

    for key in key_list_operate:
        dummy = get_keychain(key)
        if dummy:
            if len(dummy) > 1:
                path = '.'.join(dummy)
                result.append(path)
            elif len(dummy) == 1: # key at first level
                path = dummy[0]
                result.append(path)
        else:  # find an empty dictionary
            path = key
            result.append(path)
        if verbose:
            print('keychain to your desired key %s is "%s"' % (key, path))
        else:
            pass
    return result

def search(desired_value, *args, **kwargs):
    '''Return all possible header(s) that satisfy your searching criteria

    this function operates in two logics:
    1) When desired_value and args are both given. It will search on all headers matches args = desired_value.
        args can be incomplete and in this case, this function yields multiple searches

    example:
    desired_value = 'TiO2'
    search(desired_value, *'sa') will return all headers that has keys starting with 'sa' and its corresponding
    values is 'TiO2' in metadata dictionary. Nanmely, it yields searchs on headers with sample = TiO2, sadness = TiO2 ...

    2) When desired_value is not given. It implies you already knew your searching criteria and are ready to type them explicitly,
        even with additional constrains.

    example:
    desired_value = 'TiO2'
    search (False, **{'sample_name':desired_value, 'additonal_field': 'additional_value ....}) will return
    headers that have exactly key pairs **{'sample_name':desired_value, 'additonal_field': 'additional_value ....}

    General stratege is to use the first logic to figure out what is your desired key.
    Then user the second logic to restrain your search

    arguments:
    desired_value - str - desired value you are looking for
    args - str - key name you want to search for. It can be fuzzy or complete. If it is fuzzy, all possibility will be listed.
    kwargs - dict - an dictionary that contains exact key-value pairs you want to search for

    '''
    if desired_value and args:
        possible_keys = get_keys(args)
        keychain_list = build_keychain_list(possible_keys, verbose =0)
        search_header_list = []
        for i in range(len(keychain_list)):
            dummy_search_dict = {}
            dummy_search_dict[keychain_list[i]] = desired_value
            dummy_search_dict['group'] = 'XPD' # create an anchor as mongoDB and_search needs at least 2 key-value pairs
            search_header = db(**dummy_search_dict)
            search_header_list.append(search_header)
            print('Your %ith search "%s=%s" yields %i headers' % (i,
                keychain_list[i], desired_value, len(search_header)))
            return search_header_list
    elif not desired_value and kwars:
        if len(kwargs)>1:
            search_header = db(**kwargs)
        elif len(kwargs) == 1:
            kwargs['group'] = 'XPD'
            search_header = db(**kwargs)
        else:
            print('You gave empty search criteria. Please try again')
            return
        return search_header
    else:
        print('Sorry, your search is somehow unrecongnizable. Please make sure you are putting values to right fields')


