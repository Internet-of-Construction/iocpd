# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 11:12:33 2022

@author: GarlefHupfer
"""

import pickle
import pandas

def get_updates(processes, new_processes):
    updates = check_updates(processes, new_processes)
    
    event_log_add = pandas.DataFrame(columns=['process', 'key', 'from', 'to', 'timestamp'])
    
    for key in updates.keys():
        for k in updates[key].keys():
            if k == 'timestamp':
                continue
            
            d = {}
            d['process'] = [key]
            d['key'] = [k]
            d['from'] = [updates[key][k][0]]
            d['to'] = [updates[key][k][1]]
            d['timestamp'] = [updates[key]['timestamp']]
            
            df = pandas.DataFrame(d)
            event_log_add = pandas.concat([event_log_add, df], ignore_index=True, axis=0)
    
    return event_log_add


def check_updates(processes, new_processes):
    updates = {}
    
    for i in range(processes.shape[0]):
        process = processes.iloc[i]
        
        # every process in old is still existing in the new one
        if not process['processname'] in list(new_processes['processname']):
            print(f'WARNING: Illegal transition of processes, process {process["processname"]} does not exist in updated processes')
        
        new_process = new_processes.iloc[list(new_processes['processname']).index(process['processname'])]
        
        if not pickle.dumps(process) == pickle.dumps(new_process):
            updates[process['processname']] = {}
        
            # get transitions of states
            for key in process.keys():
                if not process[key] == new_process[key]:
                    updates[process['processname']][key] = (process[key], new_process[key])
            updates[process['processname']]['timestamp'] = process['statustmstp']
    
    # get new processes
    if new_processes.shape[0] > processes.shape[0]:
        for i in range(new_processes.shape[0]):
            new_process = new_processes.iloc[i]
            
            if not new_process['processname'] in list(new_processes['processname']):
                for key in new_process.keys():
                    updates[new_process['processname']][key] = (None, new_process['key'])
    
    # check if code is correct, i.e., no illegal transitions
    for key in updates.keys():
        isstarted = updates[key].get('isstarted') or (None, None)
        isfinished = updates[key].get('isfinished') or (None, None)
        
        if isstarted[0] and not isstarted[1]:
            raise Exception(f'Illegal state transition at process {key} from true to false in isstarted')
        
        if isfinished[0] and not isfinished[1]:
            raise Exception(f'Illegal state transition at process {key} from true to false in isfinished')
        
    return updates