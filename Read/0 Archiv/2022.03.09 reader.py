# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 11:05:07 2022

@author: GarlefHupfer
"""

import numpy as py
import pm4py
import os
import pandas as pd
from collections import Counter
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.statistics.sojourn_time.log import get as soj_time_get
from pm4py.statistics.traces.generic.log import case_statistics
import json


def get_value(activity, key):
    val = activity.get(key, None)
    
    if val:
        return val['value']
    else:
        return None

    
def get_df(path):
    f = open(path)
    results = json.load(f)
    f.close()
    
    activities = results['results']['bindings']
    globals()['js'] = activities
    
    keys = list(activities[0].keys()) + ['case:concept:name']
    
    
    df = pd.DataFrame(columns=keys)
    
    for activity in activities:
        d = {}
        for key in keys:
            d[key] = [get_value(activity, key)]
        d['case:concept:name'] = 1
        df2 = pd.DataFrame(d)
        df = pd.concat([df, df2], ignore_index=True, axis=0)
    
    return df

#------------------------------------------------------------------------------
# Importing log (CSV)
#------------------------------------------------------------------------------
#%%
def get_log_from_path(path, sep = '|', header = 0, time_stamp = 'time:timestamp'):
    log_csv = pd.read_csv(path, sep=sep, header=header, encoding='windows-1252')
    
    log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
    log_csv = log_csv.sort_values(time_stamp)
    
    return log_converter.apply(log_csv)


#%%
def get_dfg(log, variant = dfg_discovery.Variants.PERFORMANCE):
    return dfg_discovery.apply(log, variant=variant)


def get_soj_time(log, parameters={}):
    return soj_time_get.apply(log=log, parameters=parameters)
    

def substract_soj_time_from_dfg(dfg, soj_time):
    dfg_dict = dict(dfg)

    for key in dfg_dict.keys():
        dfg_dict[key] = py.maximum(dfg_dict[key] - soj_time[key[1]], 0)

    return Counter(dfg_dict)


def visualize_dfg(dfg, log, variant = dfg_visualization.Variants.PERFORMANCE, parameters = {}):
    gviz = dfg_visualization.apply(dfg, log=log, variant=variant, parameters=parameters)
    dfg_visualization.view(gviz)



#%% Analysis of logs
def get_statistics(log):
    soj_time = get_soj_time(log, parameters={pm4py.statistics.sojourn_time.log.get.Parameters.START_TIMESTAMP_KEY: 'start_timestamp'})
    all_case_durations = case_statistics.get_all_casedurations(log, parameters={case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    return soj_time, all_case_durations



log = get_df('processes.json')
log = log.rename(columns={'endtime': 'time:timestamp', 'processname': 'concept:name'})
dfg = get_dfg(log)
visualize_dfg(dfg, log)

soj_time_base, case_dur_base = get_statistics(log)
for key in soj_time_base.keys():
    soj_time_base[key] /=  3600

case_dur_base = [t / 3600 for t in case_dur_base]