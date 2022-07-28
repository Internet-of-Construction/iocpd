# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 20:22:39 2021

@author: GarlefHupfer
"""

import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.2 Quantifizierung des Nutzens')

import numpy as py
import time
import datetime
from datetime import timedelta
from io import BytesIO
import random
from xml.etree import ElementTree
import ast
import uuid
import copy
import time

import LeanSpiffWorkflow
from LeanSpiffWorkflow.workflow import Workflow
from LeanSpiffWorkflow.task import Task
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.serializer.Packager import Packager
from SpiffWorkflow.exceptions import WorkflowException

#testing area
def get_wf_spec_from_path(path):
    ETRoot = ElementTree.parse(path).getroot()
    
    processElements = []
    
    for child in ETRoot:
        if child.tag.endswith('process'): #and (child.attrib.get('isExecutable', False) == 'false'):
            processElements.append(child)
    
    if len(processElements) == 0:
        raise Exception('No executable process tag found')
        
    if len(processElements) > 1:
        raise Exception('Multiple executable processes tags found')
    
    processID = processElements[0].attrib['id']
    
    s = BytesIO()
    packager = Packager(s, processID)
    packager.add_bpmn_file(path)
    packager.create_package()
    package = s.getvalue()
    
    return BpmnSerializer().deserialize_workflow_spec(package)


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# BPMNRunner
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#%%
class BPMNRunner():
    def __init__(self, wf_spec_path, output_file, **kwargs):
        # needed args: wf_spec and output_file
        self.wf_spec_path = wf_spec_path
        self.output_file = output_file
        
        # times for work and transmission times
        self.get_time = kwargs.get('get_time') or self.get_time_default
        self.get_transmission_time = kwargs.get('get_transmission_time') or self.get_transmission_time_default
        
        # impairing the logs
        self.impair_data_availability_bool = kwargs.get('impair_data_availability') or False
        self.impair_data_availability_probability = kwargs.get('impair_data_availability_probability') or 0.5
        
        # arguments for log generation
        self.start_time = kwargs.get('start_time') or datetime.datetime.now()
        self.write_gateways = kwargs.get('write_gateways') or False
        self.include_partner_in_activity_name = kwargs.get('include_partner_in_activity_name') or False
        
        
    #------------------------------------------------------------------------------
    # Case Creation
    #------------------------------------------------------------------------------
    # create mulitple cases
    def create_cases(self, n, append=False, first_case_id=1):
        if not append:
            f = open(self.output_file, 'w')
            f.write('case:concept:name|concept:name|start_timestamp|time:timestamp|partner\n')
            f.close()
        
        # prepare datetime deltas
        start_time = self.start_time
        
        for i in range(first_case_id, n):
            print('current case: %i / %i' %(i, n))
            
            # reset the possibly impaired logs
            self.wf_spec = get_wf_spec_from_path(self.wf_spec_path)

            if self.impair_data_availability_bool:
                self.impair_data_availability()
            
            self.create_case(i, start_time)
            start_time = start_time + timedelta(days = py.random.normal(1, 0.1))
    
    
    # creating a single case
    def create_case(self, case_id, start_time):
        self.wf = Workflow(self.wf_spec)
        self.starting_times = {'Start': start_time}
        self.completion_times = {'Start': (start_time + timedelta(seconds = 1))}
        
        
        f = open(self.output_file, 'a')
        
        while not self.wf.is_completed():
            readys = self.wf.get_tasks(Task.READY)
            flag = readys[0].task_spec
            
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
                
                self.calculate_times(gateways[0])
                
                if  len(gateways[0].children) > 1:
                    gateways[0].set_state(Task.COMPLETED)
                else:
                    gateways[0].complete()
                
                self.write_log_line(f, case_id, gateways[0])
                
                continue
            
            # complete all ready tasks, calculate starting and completion times and save to log
            #-----------------------------------------------------------------
            for t in readys:
                self.calculate_times(t)
                self.wf.complete_task_from_id(t.id)
                
                self.write_log_line(f, case_id, t)
        
        f.close()
    
    
    def write_log_line(self, file, case_id, task):
        # If not write_gateways then only write NoneTasks and Simples        
        if (not self.write_gateways and type(task.task_spec).__name__ not in ['NoneTask', 'Simple', 'StartEvent']):
            return
        if (task.task_spec.description == None):
            if type(task.task_spec).__name__ == 'StartEvent':
                task.task_spec.description = 'Start'
            else:
                return
        
        # get partner
        lane = getattr(task.task_spec, 'lane', '')
        
        # print activity description and identifier (for the case of two tasks named identically)
        activity = ('%s (%s)') % (task.task_spec.description.replace('\n', ' '), task.task_spec.name[-7:])
        
        if self.include_partner_in_activity_name and lane != '':
            activity = lane + ' ' + activity
        
        file.write('%i|%s|%s|%s|%s\n'% (case_id, activity, self.starting_times[task.get_name()], self.completion_times[task.get_name()], lane))
    
    
    # Helper functions for calculating times
    #------------------------------------------------------------------------------
    def calculate_times(self, task):
        starting_time = self.get_first_possible_starting_time(task)
        self.starting_times[task.get_name()] = starting_time
        
        completion_time = starting_time + self.get_time(task.task_spec.description)
        self.completion_times[task.get_name()] = completion_time
    
    # get time, when last parent was completed + time between tasks informations
    def get_first_possible_starting_time(self, task):
        parents = list(set(self.get_parents(task)) & set(self.wf.get_tasks(state=Task.COMPLETED)))
        
        if len(parents) == 0:
            # after a gateway; simply take the single parent, which is the gateway
            parents = task.parents
            
        return max([(self.completion_times[p.task_spec.name] + self.get_transmission_time(p.task_spec)) for p in parents])
    
    # get all parents of a task
    def get_parents(self, task):
        return [t for t in self.wf.tasks if (t.task_spec in task.task_spec.inputs)]
    
    # get time needed for a task
    def get_time_default(self, task_spec):
        return timedelta(seconds=1)
    
    # get time needed between finish of one task and following one
    def get_transmission_time_default(self, task_spec):
        return timedelta(seconds=1)
    #------------------------------------------------------------------------------
    # Impair the logs
    #------------------------------------------------------------------------------
    # Add task loop for getting information
    #------------------------------------------------------------------------------
    # information is not available when the task is started
    def impair_data_availability(self):
        for task_spec in list(self.wf_spec.task_specs.values()):
            if task_spec.description == None:
                continue
            
            if self.is_desk_work_task(task_spec):
                # get all ingoing information nodes
                information_inputs = self.get_information_inputs(task_spec)
                
                is_information_missing = []
                
                for information in information_inputs:
                    is_information_missing.append(py.random.binomial(1, self.impair_data_availability_probability))
                    
                if sum(is_information_missing) == 0:
                    print('bad luck')
                    break
                
                
                # save current next node and disconnect nodes
                next_task = task_spec.outputs[0]
                task_spec.outputs = []
                next_task.inputs.remove(task_spec)
                
                # TODO: change working time for current task
                # AND change times needed for getting the information
                original_desk_work_desc = task_spec.description
                task_spec.description = (task_spec.description + '(only checking for information)').replace('[deskwork]\n', '')
                self.times[task_spec.description] = (0.1, 0.001)
                
                
                # add a parallel gateway
                parallel = MultiChoice(self.wf_spec, str(uuid.uuid4()))
                parallel.description= 'parallelOpen'
                task_spec.connect(parallel)
                
                #save all added nodes
                information_sending_nodes = []
                
                for i in range(len(is_information_missing)):
                    if is_information_missing[i] == 1:
                        # add task needed for asking for information (same partner)
                        random.seed(task_spec.name + information_inputs[i].name)
                        ask_for_information = Simple(self.wf_spec, name=str(uuid.UUID(int=random.getrandbits(128))))
                        ask_for_information.description = '[Information einholen]' + information_inputs[i].description.replace('[information]\n', ' ')
                        self.times['[Information einholen]' + information_inputs[i].description.replace('[information]\n', ' ')] = (0.1, 0.001)
                        self.transmission_times['[Information einholen]' + information_inputs[i].description.replace('[information]\n', ' ')] = (2, 0.1)
                        ask_for_information.lane = task_spec.lane
                        parallel.connect(ask_for_information)
                        
                        # add task needed for sending information (different partner)
                        random.seed(task_spec.name + information_inputs[i].name + '2')
                        send_information = Simple(self.wf_spec, name=str(uuid.UUID(int=random.getrandbits(128))))
                        send_information.description = '[Information senden]' + information_inputs[i].description.replace('[information]\n', ' ')
                        self.times['[Information senden]' + information_inputs[i].description.replace('[information]\n', ' ')] = (0.1, 0.001)
                        self.transmission_times['[Information senden]' + information_inputs[i].description.replace('[information]\n', ' ')] = (2, 0.1)
                        send_information.lane = information_inputs[i].lane
                        ask_for_information.connect(send_information)
                        
                        information_sending_nodes += [send_information]
                
                # add a closing parallel gateway
                parallel_close = Join(self.wf_spec, str(uuid.uuid4()))
                parallel_close.description = 'parallelClose'
                
                for task in information_sending_nodes:
                    task.connect(parallel_close)
                
                # add a final task which is the actual task and has been changed above
                random.seed(task_spec.name)
                actual_task = Simple(self.wf_spec, name=str(uuid.UUID(int=random.getrandbits(128))))
                actual_task.description = original_desk_work_desc
                actual_task.lane = task_spec.name
                parallel_close.connect(actual_task)                
                
                # connect this final task to the old next_task
                actual_task.connect(next_task)
                
                
    # Helper functions
    #------------------------------------------------------------------------------
    def get_task_type(self, task_spec):
        if (task_spec.description == None):
            return None
        if (task_spec.description.find('[') ==- -1):
            return 'Unknown'
        
        return task_spec.description[task_spec.description.find('['):].replace('[', '').replace(']', '')
    
    
    # search for all inputs that are informations BUT also include everything that may be behind a gateway
    def get_information_inputs(self, task_spec):
        information_inputs = []
        
        for parent_task_spec in task_spec.inputs:
            information_inputs += self._get_information_inputs(parent_task_spec)
        
        return information_inputs
        
    
    def _get_information_inputs(self, task_spec):
        #TODO: need unique classification when to stop searching further, e. g. everything but a gateway
        if type(task_spec).__name__ in ["ExclusiveGateway", "ParallelGateway"]:
            information_inputs = []
            
            for parent_task_spec in task_spec.inputs:
                information_inputs += self._get_information_inputs(parent_task_spec)
            
            return information_inputs
        if self.get_task_type(task_spec) == 1:
            #TODO: Implement all values correctly:
            return [task_spec]
        
        return []
    
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# Creating a log
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#%%
def create_log(bpmn_path, output_file, n, **kwargs):
    # get the runner to work with
    runner = BPMNRunner(bpmn_path, output_file, **kwargs)
    
    # sometimes, a permission error is raised. Therefore, we are looping over create_cases while always passing the current
    # case_id
    append = kwargs.get('append') or False
    first_case_id = kwargs.get('first_case_id') or 1
    
    while True:
        try:
            runner.create_cases(n, append=append, first_case_id=first_case_id)
            break
        except PermissionError:
            print('Coulnd\'t access file, retrying...')
            time.sleep(1)
            
            append=True
            file = open(output_file, 'r')
            for last_line in file:
                pass
            
            first_case_id = int(last_line[:last_line.find('|')]) + 1


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------                

#------------------------------------------------------------------------------
# Time functions
#------------------------------------------------------------------------------
#%%
def get_time(task_spec):
    # TODO
    print('')

def get_transmisison_time(task_spec):
    # TODO
    print('')

def get_task_type(task_spec):
    if (task_spec.description == None):
        return None
    if (task_spec.description.find('[') ==- -1):
        return 'Unknown'
    
    return task_spec.description[task_spec.description.find('['):].replace('[', '').replace(']', '')

#%%
def main():
    os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.2 Quantifizierung des Nutzens')
    
    bpmn_path = '5 LogCreation/bpmns/Informationslandkarte v3.bpmn'
    
    # clean log
    create_log(bpmn_path, output_file='5 LogCreation/logs/lean_log.csv', n=10)
    
main()