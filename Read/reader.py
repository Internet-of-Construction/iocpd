# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 11:05:07 2022

@author: GarlefHupfer
"""

import json
import pandas as pd
from datetime import datetime

def get_processes_from_path(path):
    f = open(path)
    j = json.load(f)
    f.close()
    
    return get_processes_from_json(j)
    

def get_processes_from_json(j):
    if type(j).__name__ == 'str':
        j = json.loads(j)
    
    activities = j['results']['bindings']
    
    ids = []
    rmv = []
    
    # clean doubles
    for a in activities:
        i = get_value(a, 'process')
        
        if i in ids:
            forks = [act for act in activities if get_value(act, 'process') == i]
            main = forks[0]
            print(f'processtmstp {[f["processtmstp"]["value"][:19] for f in forks]}')
            print(f'statustmstp {[f["statustmstp"]["value"][:19] for f in forks]}')
            print(f'starttime {[f["starttime"]["value"][:19] for f in forks]}')
            print(f'endtime {[f["endtime"]["value"][:19] for f in forks]}')
            
            main['processtmstp']['value'] = min([datetime.strptime(f['processtmstp']['value'][:19], '%Y-%m-%dT%H:%M:%S') for f in forks]).strftime('%Y-%m-%d %H:%M:%S')
            main['statustmstp']['value'] = min([datetime.strptime(f['statustmstp']['value'][:19], '%Y-%m-%dT%H:%M:%S') for f in forks]).strftime('%Y-%m-%d %H:%M:%S')
            main['starttime']['value'] = min([datetime.strptime(f['starttime']['value'][:19], '%Y-%m-%d %H:%M:%S') for f in forks]).strftime('%Y-%m-%d %H:%M:%S')
            main['endtime']['value'] = min([datetime.strptime(f['endtime']['value'][:19], '%Y-%m-%d %H:%M:%S') for f in forks]).strftime('%Y-%m-%d %H:%M:%S')
            
            isstarted = [f['isstarted']['value'] for f in forks]
            main['isstarted']['value'] = str(('true' in isstarted)).lower()
            
            isfinished = [f['isstarted']['value'] for f in forks]
            main['isstarted']['value'] = str(not ('false' in isfinished)).lower()
            
            res = [f['resdescription']['value'] for f in forks]
            main['resdescription']['value'] = str(list(dict.fromkeys(res))).replace('"', '').replace(',', '|')
            
            for f in forks[1:]:
                if not f in rmv:
                    rmv.append(f)
        else:
            ids.append(i)
            
    for r in rmv:
        activities.remove(r)
    
    keys = list(activities[0].keys()) + ['case:concept:name']
    df = pd.DataFrame(columns=keys)
    
    for activity in activities:
        d = {}
        for key in keys:
            d[key] = [get_value(activity, key)]
        
        d['case:concept:name'] = 0
        df2 = pd.DataFrame(d)
        df = pd.concat([df, df2], ignore_index=True, axis=0)
    
    return df


def get_value(activity, key):
    val = activity.get(key, None)
    
    if val:
        return val['value']
    else:
        return None