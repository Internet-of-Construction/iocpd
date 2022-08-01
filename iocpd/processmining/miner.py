# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 11:05:07 2022

@author: GarlefHupfer
"""

import os
import numpy as py
import pm4py
import ast
import pandas as pd
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.statistics.sojourn_time.log import get as soj_time_get
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.algo.discovery.temporal_profile import algorithm as temporal_profile_discovery
from pm4py.objects.conversion.bpmn import converter as bpmn_converter
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.conversion.process_tree import converter as process_tree_converter

class Miner():
    def __init__(self, project_path, log_path, **kwargs):
        self.project_path = project_path
        self.log_path = log_path
        
        self.sep = kwargs.get('sep') or '|'
        self.header = kwargs.get('header') or 0
        self.encoding = kwargs.get('encoding') or 'windows-1252'
        self.concept_name = kwargs.get('concept_name') or 'concept:name'
        self.timestamp = kwargs.get('timestamp') or 'time:timestamp'
        self.start_timestamp = kwargs.get('timestamp') or 'start:time:timestamp'
        self.case_concept_name = kwargs.get('case_concept_name') or 'case:concept:name'
        self.log = self.get_log()
        
        self.bpmn_path = kwargs.get('bpmn_path') or None
        if self.bpmn_path:
            self.bpmn_graph = pm4py.read_bpmn(self.bpmn_path)
        else:
            self.bpmn_graph = self.get_bpmn_from_log()
            pm4py.write_bpmn(self.bpmn_graph, project_path + 'generated_project_bpmn.bpmn', enable_layout=True)
            
        self.cost_types = kwargs.get('cost_types') or None
        
    def get_log(self):
        log_csv = pd.read_csv(self.log_path, sep=self.sep, header=self.header, encoding=self.encoding)
        log_csv = log_csv.rename(columns={self.concept_name: 'concept:name', self.timestamp: 'time:timestamp', self.start_timestamp: 'start:time:timestamp'})
        log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
        log_csv = log_csv.sort_values('time:timestamp')
        return log_converter.apply(log_csv)
    
    def get_times_and_transmission_times(self):
        soj_time = self.get_soj_time()
        dfg_times = self.subtract_soj_time_from_dfg(self.get_dfg(), soj_time)
        transmission_times = self.get_transmission_times(self.get_activities(), dfg_times)
        with open(self.project_path + 'times.cfg', 'w+') as f: 
            f.write('{\n')
            for key, value in soj_time.items():
                f.write(f'\'{key}\': ({value}, {value/10}),\n')
            f.write('\'end\': (0, 0)\n}')
            f.close()
        with open(self.project_path + 'transmission_times.cfg', 'w+') as f: 
            f.write('{\n')
            for key, value in transmission_times.items():
                f.write(f'\'{key}\': ({value}, {value/10}),\n')
            f.write('\'end\': (0, 0)\n}')
            f.close()
    
    def get_activities(self):
        log_csv = pd.read_csv(self.log_path, sep=self.sep, header=self.header, encoding=self.encoding)
        log_csv = log_csv.rename(columns={self.concept_name: 'concept:name', self.timestamp: 'time:timestamp', self.start_timestamp: 'start:time:timestamp'})
        activities = log_csv['concept:name'].to_list()
        return list(dict.fromkeys(activities))
    
    def get_dfg(self, variant = dfg_discovery.Variants.PERFORMANCE):
        dfg = dict(dfg_discovery.apply(self.log, variant=variant))
        for key in dfg.keys():
            dfg[key] /= 3600
        return dfg
    
    def get_soj_time(self, parameters={soj_time_get.Parameters.TIMESTAMP_KEY: "time:timestamp", soj_time_get.Parameters.START_TIMESTAMP_KEY: "start:time:timestamp"}):
        soj_time = soj_time_get.apply(log=self.log, parameters=parameters)
        for key in soj_time.keys():
            soj_time[key] = py.round(soj_time[key] / 3600, 1)
        return soj_time

    def subtract_soj_time_from_dfg(self, dfg, soj_time):
        for key in dfg.keys():
            dfg[key] = py.maximum(dfg[key] - soj_time[key[1]], 0)
        return dfg
    
    def get_transmission_times(self, activities, dfg_times):
        transmission_times = {}
        for activity in activities:
            transmission_times[activity] = py.mean([dfg_times[key] for key in dfg_times.keys() if key[0] == activity])
        return transmission_times
    
    def visualize_dfg(self, dfg, variant = dfg_visualization.Variants.PERFORMANCE, parameters = {}):
        gviz = dfg_visualization.apply(dfg, log=self.log, variant=variant, parameters=parameters)
        dfg_visualization.view(gviz)

    def get_case_dur(self):
        case_durations = case_statistics.get_all_casedurations(self.log, parameters={case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
        return [dur / 3600 for dur in case_durations]
    
    def get_costs(self):
        log_csv = pd.read_csv(self.log_path, sep=self.sep, header=self.header, encoding=self.encoding)
        log_csv = log_csv.rename(columns={self.concept_name: 'concept:name', self.timestamp: 'time:timestamp', self.start_timestamp: 'start:time:timestamp'})
        log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
        costs = log_csv['costs'].astype('str')
        costs = costs.apply(lambda x: ast.literal_eval(x))
        costs = costs.apply(pd.Series)
        log_csv = pd.concat([log_csv.drop(['costs'], axis=1), costs], axis=1)
        
        return log_csv.groupby(['case:concept:name']).sum()
    
    def get_costs2(self):
        log_csv = pd.read_csv(self.log_path, sep=self.sep, header=self.header, encoding=self.encoding)
        log_csv = log_csv.rename(columns={self.concept_name: 'concept:name', self.timestamp: 'time:timestamp', self.start_timestamp: 'start:time:timestamp'})
        log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
        log_csv = log_csv.sort_values('time:timestamp')
        
        costs = log_csv['costs'].astype('str')
        costs = costs.apply(lambda x: ast.literal_eval(x))
        costs = costs.apply(pd.Series)
        
        log_csv = pd.concat([log_csv.drop(['costs'], axis=1), costs], axis=1)
        return log_csv.groupby(['concept:name']).mean()
    
    def get_bpmn_from_log(self):
        tree = pm4py.discover_process_tree_inductive(self.log)
        return process_tree_converter.apply(tree, variant=process_tree_converter.Variants.TO_BPMN)
    
    def get_temporal_profile(self):
        return temporal_profile_discovery.apply(self.log)

    def save_petri_net(self, path):
        self.net, self.im, self.fm = bpmn_converter.apply(self.bpmn_graph)
        pnml_exporter.apply(self.net, self.im, path)
