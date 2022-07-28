"""
Created on Tue Mar 14 13:56:20 2022

@author: GarlefHupfer
"""

"""
The Logic of creating the log

- Importing all the stuff
- Helper function: get_wf_spec_from_path
- BPMN Runner:
    - init
    creating the BPMN-Runner, saving all variables
    - create cases:
        - logic around creating a single case multiple times
        - simulate the log several times in order to get a schedule
    - create case:
        - reading the wf_spec
        - manipulating the wf_spec regarding impairment
        - creating the wf
        - simulating the wf
    - all helper functions
        - calculate_times
        - get_first_possible_starting_time
        - impairment functions
 - create log
    logic around utilizing the BPMN-runner in order to get a log out of a bpmn
- main
    utilizing create log to get different logs with several problems
"""

# %%
import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')

import numpy as py
import datetime
from datetime import timedelta
import random
import pandas
from ConfigReader.configreader import get_config

from LeanSpiffWorkflow.workflow import Workflow
from LeanSpiffWorkflow.task import Task
from LeanSpiffWorkflow.getwfspec import get_wf_spec
from SpiffWorkflow.exceptions import WorkflowException
from Miner.miner import Miner

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# BPMNRunner
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
class Runner():
    def __init__(self, project_path, bpmn_path, config_path, **kwargs):
        # needed args: wf_spec, output_file and config
        self.bpmn_path = bpmn_path
        self.config = get_config(config_path)
        self.times = kwargs.get('times') or {}
        self.transmission_times = kwargs.get('transmission_times') or {}
        self.costs = kwargs.get('costs') or {}
        self.monte_carlo_n = kwargs.get('monte_carlo_n') or 50
        self.cost_types = kwargs.get('cost_types') or None
        
        self.project_path = project_path
        self.current_processes = kwargs.get('current_processes')
        if self.current_processes is None:
            pandas.DataFrame(columns=['process', 'processtmstp', 'statustmstp', 'isfinished', 'resdescription', 'processauthor', 'processname', 
                                      'endtime', 'isstarted', 'starttime', 'case:concept:name'])
        
        # create wf_spec once, check its correctness and get a schedule
        self.wf_spec = get_wf_spec(self.bpmn_path, times=self.times, transmission_times=self.transmission_times, costs=self.costs, cost_types=self.cost_types)
        
        if self.cost_types == None:
            self.cost_types = []
            for task_spec in self.wf_spec.task_specs:
                costs = task_spec.data.get('costs', [])
                for cost_type in costs.keys():
                    if not cost_type in self.cost_types:
                        self.cost_types.append('cost_type')
        
        # arguments for log generation
        self.start_time = kwargs.get('start_time') or datetime.datetime.now()
        self.wf = Workflow(self.wf_spec)
    
    def update_processes(self, processes):
        self.current_processes = processes
        self.apply_processes(self.current_processes)
    
    def apply_processes(self, processes):
        self.wf = Workflow(self.wf_spec)
        
        #m = datetime.datetime.strptime('01.01.2050', '%d.%m.%Y')
        #for i in range(processes.shape[0]):
        #    print(f"{i}, {type(processes.at[i, 'statustmstp'])}, {processes.at[i, 'statustmstp']}")
        #    mi = datetime.datetime.strptime(processes.iloc[i]['statustmstp'], '%Y-%m-%d %H:%M:%S')
        #    if mi < m:
        #        m = mi
        assert type(processes).__name__ == 'DataFrame'
        
        if not processes.shape[0] == 0:
            m = min([datetime.datetime.strptime(val, '%d.%m.%Y %H:%M') for val in processes['statustmstp']])
        else:
            m = datetime.datetime.now()
        
        self.wf.start.starting_time = m
        self.wf.start.completion_time = self.wf.start.starting_time + timedelta(seconds = 1)
        self.wf.start.transmitted_time = self.wf.start.completion_time + timedelta(seconds = 1)
        self.wf.start.complete()
        
        descs = [t.description for t in list(self.wf_spec.task_specs.values())]
        for i in range(processes.shape[0]):
            process = processes.iloc[i]
            desc = process['processname']
            if not desc in descs:
                continue
            if not process['isfinished']:
                continue
            for t in self.wf.tasks:
                if t.get_description() == desc:
                    completion_time = datetime.datetime.strptime(process['statustmstp'], '%d.%m.%Y %H:%M')
                    self.wf.complete_task_from_id(t.id, force_prior=True, completion_time=completion_time)
    
    def get_next_activities_with_relevance(self):
        next_activities_list = self.get_next_activities()
        relevance = self.get_relevance(next_activities_list, self.current_processes)
        
        next_activities = pandas.DataFrame(columns=['activity', 'until', 'relevance', 'started', 'starttime'])
        for act in next_activities_list:
            d = {}
            d['activity'] = [act.get_description()]
            d['until'] = ['']
            for i in range(self.current_processes.shape[0]):
                if self.current_processes.iloc[i]['processname'] == act.get_description():
                    d['until'] = [self.current_processes.iloc[i]['endtime']]
                    d['started'] = [self.current_processes.at[i,'isstarted']]
                    d['starttime'] = [self.current_processes.at[i,'starttime']]
            d['relevance'] = [py.round(relevance[act.get_description()], 3)]
            df = pandas.DataFrame(d)
            next_activities = pandas.concat([next_activities, df], ignore_index=True, axis=0)
        
        return next_activities.sort_values('relevance', ascending=False)
        
    def get_next_activities(self):
        readys = self.wf.get_tasks(state=2)
        
        next_activities = []
        for r in readys:
            if not r in next_activities:
                next_activities.append(r)
            for c1 in r.children:
                if not c1 in next_activities:
                    next_activities.append(c1)
                for c2 in c1.children:
                    if not c2 in next_activities:
                        next_activities.append(c2)
                    #for c3 in c2.children:
                    #    if not c3 in next_activities:
                    #        next_activities.append(c3)
                        #for c4 in c3.children:
                        #    if not c4 in next_activities:
                        #        next_activities.append(c4)
        return [a for a in next_activities if not a.get_description() == 'None']
        
    def get_relevance(self, next_activities, processes):
        if len(next_activities) == 1:
            return {next_activities[0].get_description(): 1}
        
        norm = self.get_prognosis(processes)[0]
        relevances = {}
        
        for act in next_activities:
            self.apply_processes(processes)
            self.create_cases(n=self.monte_carlo_n, output_file=self.project_path + 'temp/log_runner.csv', processes=processes, to_impair=act)
            miner = Miner(self.project_path + 'temp/log_runner.csv', self.bpmn_path, self.project_path)
            case_dur = miner.get_case_dur()
            
            mean_diff = py.mean(case_dur) - py.mean(norm)
            relevances[act.get_description()] = py.round(mean_diff, 3)
        
        relevance = {}
        for key in relevances:
            relevance[key] = (relevances[key] - min(list(relevances.values()))) / (max(list(relevances.values())) - min(list(relevances.values()))) #max(min(relevances[key]/10, 1), 0)
        
        return relevance
    
    def get_prognosis(self, processes, n=50):
        self.create_cases(n=n, output_file=self.project_path + 'temp/log_runner.csv', processes=processes)
        miner = Miner(self.project_path + 'temp/log_runner.csv', self.bpmn_path, self.project_path, cost_types=self.cost_types)
        return [miner.get_case_dur(), miner.get_costs()]
    
    
    def create_cases(self, n, output_file, processes, append=False, first_case_id=1, **kwargs):
        # open file to write
        if not append:
            f = open(output_file, 'w+')
            f.write('case:concept:name|concept:name|start_timestamp|time:timestamp|partner|costs\n')
            f.close()
        
        # create all the cases
        for i in range(first_case_id, n+1):
            #print('current case: %i / %i' %(i, n))
            self.apply_processes(processes)
            
            to_impair = kwargs.get('to_impair') or None
            if to_impair:
                tsk = self.wf.get_task_by_task_id(to_impair.get_name())
                #print(f'found tsk {tsk.get_name()}')
                tsk.time = (tsk.time[0] + i, tsk.time[1])
            
            self.create_case(output_file, i)
    
    
    # creating a single case
    def create_case(self, output_file, case_id):
        self.f = open(output_file, 'a')
        
        while not self.wf.is_completed():
            readys = self.wf.get_tasks(Task.READY)
            
            if not readys:
                raise WorkflowException(self.wf_spec, 'no ready tasks')

            for t in readys:
                self.calculate_times(t)
                self.calculate_costs(t)
                self.wf.complete_task_from_id(t.id)
                self.write_log_line(case_id, t)
        
        self.f.close()
    
    
    # Helper functions
    #------------------------------------------------------------------------------
    # calculate times when task can be completed as well as completion and transmission times
    def calculate_times(self, task):
        task.starting_time = self.get_first_possible_starting_time(task)
        task.completion_time = task.starting_time + task.get_time()
        task.transmitted_time = task.completion_time + task.get_transmission_time()
        
    # get time, when last parent was completed + time between tasks informations
    def get_first_possible_starting_time(self, task):
        return max([p.transmitted_time for p in [parent for parent in task.parents if parent.is_completed()]])
    
    def calculate_costs(self, task):
        task.cost = task.get_costs()
    
    # log all data of some task
    def write_log_line(self, case_id, task):
        # If not write_gateways then only write NoneTasks and Simples        
        if (type(task.task_spec).__name__ not in ['NoneTask', 'Simple', 'StartEvent']):
            return
        if (task.task_spec.description == None):
            if type(task.task_spec).__name__ == 'StartEvent':
                task.task_spec.description = 'Start'
            else:
                print(f'WARNING: task {task.id} does not have a description')
                return
        
        # get partner
        lane = getattr(task.task_spec, 'lane', '')
        
        # print activity description and identifier (for the case of two tasks named identically)
        activity = ('%s (%s)') % (task.task_spec.description.replace('\n', ' ').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue'), task.task_spec.name[-7:])
        
        self.f.write('%i|%s|%s|%s|%s|%s\n'% (case_id, activity, task.starting_time, task.completion_time, lane, str(task.cost)))
    
    # Schedule
    #------------------------------------------------------------------------------
    def get_schedule_and_costs(self, start_date=None, end_date=None):
        [schedule_times, costs_dict] = self.get_schedule_times_and_costs()
        if start_date and end_date:
            print('WARNING: both start and end date were given, only using start date')
            end_date = None
        elif end_date:
            start_date = self.business_hour_add(end_date, timedelta(hours=-max(schedule_times.values())))
        if not start_date:
            start_date= datetime.datetime.now()
        
        
        schedule = pandas.DataFrame(columns=['processname', 'starttime', 'endtime'])
        schedule = schedule.append({'processname': 'starttime', 'starttime': start_date.strftime('%Y-%m-%d %H:%M:%S'), 'endtime': start_date.strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)
        for key in schedule_times.keys():
            if key[1] == '' or key[1] == None:
                continue
            
            end_time = self.business_hour_add(start_date, timedelta(hours=schedule_times[key]))
            task_spec = [self.wf_spec.task_specs[k] for k in self.wf_spec.task_specs.keys() if k == key[0]]
            start_time = self.business_hour_add(end_time, timedelta(hours=-task_spec[0].data['time'][0]))
            schedule = schedule.append({'processname': key[1], 'starttime': start_time.strftime('%Y-%m-%d %H:%M:%S'), 'endtime': end_time.strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)
            
        costs = pandas.DataFrame(columns=['processname'] + [cost_type for cost_type in self.cost_types])
        for key in costs_dict.keys():
            if key[1] == '' or key[1] == None:
                continue
            
            to_append = {'processname': key[1]}
            for cost_type in self.cost_types:
                to_append[cost_type] = costs_dict[key].get(cost_type, 0)
            costs = costs.append(to_append, ignore_index=True)
        
        costs.to_csv(self.project_path + 'predicted_costs.csv')
        
        return [schedule, costs]
        
    def business_hour_add(self, date, add, start_hour=7, end_hour=16):
        if add.total_seconds() >= 0:
            while add.total_seconds() > (end_hour - start_hour) * 3600:
                date += timedelta(days=1)
                add -= timedelta(hours=end_hour-start_hour)
                
                while date.weekday() in [5, 6]:
                    date += timedelta(days=1)
            
            date += add
            
            if date.hour >= end_hour or date.hour < start_hour:
                date += timedelta(hours=(24-end_hour)+start_hour)
        
            while date.weekday() in [5, 6]:
                date += timedelta(days=1)
        else:
            while add.total_seconds() < - (end_hour - start_hour) * 3600:
                date -= timedelta(days=1)
                add += timedelta(hours=end_hour-start_hour)
                
                while date.weekday() in [5, 6]:
                    date -= timedelta(days=1)
            
            date += add
            
            if date.hour >= end_hour or date.hour < start_hour:
                date -= timedelta(hours=(24-end_hour)+start_hour)
        
            while date.weekday() in [5, 6]:
                date -= timedelta(days=1)
        
        return date
                
    
    def get_schedule_times_and_costs(self):
        start_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        completion_times={}
        costs = {}
        
        # build buffer on all actual tasks
        #for task_spec in self.wf_spec.task_specs.values():
        #    if get_type(task_spec) in ['coordination', 'request', 'send output', 'process input', 'practical', 'confirmation', 'schedule', 'desk work']:
        #        task_spec.data['transmission_time'] = (task_spec.data['time'][0] * (1 + self.config.get('buffer_per_task')), 0)
        
        for i in range(int(self.config.get('simulation_count'))):
            completion_times[f'case{i}'] = {}
            costs[f'case{i}'] = {}
            
            self.wf = Workflow(self.wf_spec)
            self.wf.start.starting_time = start_time
            self.wf.start.completion_time = self.wf.start.starting_time + timedelta(seconds = 1)
            self.wf.start.transmitted_time = self.wf.start.completion_time + timedelta(seconds = 1)
            completion_times[f'case{i}']['Start'] = self.wf.start.completion_time
            costs[f'case{i}']['Start'] = {}
            
            while not self.wf.is_completed():
                readys = self.wf.get_tasks(Task.READY)
                
                if not readys:
                    raise WorkflowException(self.wf_spec, 'no ready tasks')
                
                # Gateway Handling
                # if there is an exclusive gateway, set one child as ready and cancel the other ones
                #-----------------------------------------------------------------
                gateways = [t for t in readys if type(t.task_spec).__name__=="ExclusiveGateway" and t.state < Task.COMPLETED]
                
                if gateways:
                    surviver = random.randrange(0, len(gateways[0].children))
                    
                    for i in range(len(gateways[0].children)):
                        if i == surviver:
                            gateways[0].children[i].set_state(Task.READY)
                        else:
                            gateways[0].children[i].cancel()
                    
                    self.calculate_times_schedule(gateways[0])
                    
                    gateways[0].set_state(Task.COMPLETED)
                    completion_times[f'case{i}'][gateways[0].name] = gateways[0].completion_time
                    
                    continue
                
                #-----------------------------------------------------------------
                # complete all ready tasks, calculate starting and completion times and save to log
                #-----------------------------------------------------------------
                for t in readys:
                    self.calculate_times_schedule(t)
                    self.wf.complete_task_from_id(t.id)
                    self.calculate_costs(t)
                    
                    completion_times[f'case{i}'][t.id] = t.completion_time
                    costs[f'case{i}'][t.id] = t.cost
        
        schedule = {}
        mean_costs = {}
        
        # up until the first task, there is a general buffer, which is equal to some part of the total duration
        duration = (py.mean([completion_times[f'case{i}']['End'] - start_time for i in range(int(self.config.get('simulation_count')))])).total_seconds() / 3600 * self.config.get('buffer_to_start')
        
        for task in self.wf_spec.task_specs.values():
            schedule[(task.name, task.description)] = duration + py.mean([completion_times[f'case{i}'][task.name] - start_time for i in range(int(self.config.get('simulation_count')))]).total_seconds() / 3600
            mean_costs[(task.name, task.description)] = costs['case1'][task.name]
            for key in costs['case1'][task.name].keys():
                mean_costs[(task.name, task.description)][key] = py.round(py.mean([costs[f'case{i}'][task.name].get(key, 0) for
                                                                                   i in range(int(self.config.get('simulation_count')))]), 2)
        
        return [schedule, mean_costs]
    
    # calculate times as below, but for schedule creation, i.e., add some buffer
    def calculate_times_schedule(self, task):
        task.starting_time = self.get_first_possible_starting_time(task)
        task.completion_time = task.starting_time + task.get_time()
        if task.get_type() in ['coordination', 'request', 'send output', 'process input', 'practical', 'confirmation', 'schedule', 'desk work']:
            task.completion_time += timedelta(hours=task.time[0]) * self.config.get('buffer_per_task')
        task.transmitted_time = task.completion_time + task.get_transmission_time()