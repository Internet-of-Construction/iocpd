# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 11:05:07 2022

@author: GarlefHupfer
"""

import json
import pandas as pd
import datetime



def get_value(activity, key, default):
    val = activity.get(key, None)
    
    if val:
        return val['value']
    else:
        return default

    
def __main__():
    f = open('processes.json')
    results = json.load(f)
    f.close()
    
    activities = results['results']['bindings']
    globals()['js'] = activities
    
    df = pd.DataFrame(columns=["start", "end", "activity", "actor", 'predecessors', 'process', 'ressource', 'successors'])
    
    for activity in activities:
        start = activity.get('starttime', None)
        if start:
            start = start['value']
            start = datetime.datetime.strptime(start, '%Y-%m-%d %H.%M.%S')
        else:
            start = datetime.datetime(1970, 1, 1)
            
        end = activity.get('endtime', None)
        if end:
            end = end['value']
            end = datetime.datetime.strptime(end, '%Y-%m-%d %H.%M.%S')
        else:
            end = datetime.datetime(1970, 1, 1, 0, 0, 1)
        
        actor = get_value(activity, 'resdescription', 'No Actor defined')
        processname = get_value(activity, 'processname', 'No Processname defined')
        predecessors = get_value(activity, 'Predecessors', [])
        successors = get_value(activity, 'Successors', [])
        ressource = get_value(activity, 'Ressource', 'No Ressource defined')
        process = get_value(activity, 'Process', 'No Ressource defined')
        
        
        
        df2 = pd.DataFrame({'start': [start],
                'end': [end],
                'activity': [processname],
                'actor': [actor],
                'process': [process],
                'predecessors': [predecessors],
                'successors': [successors],
                'ressource': [ressource]})
        
        df = pd.concat([df, df2], ignore_index=True, axis=0)
    
    globals()['df'] = df
    print(df)
    


__main__()