# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 11:08:06 2022

@author: GarlefHupfer
"""

from xml.etree import ElementTree
from io import BytesIO
from SpiffWorkflow.bpmn.serializer.Packager import Packager
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.exceptions import WorkflowException

#------------------------------------------------------------------------------
# get wf_spec
#------------------------------------------------------------------------------
def get_wf_spec(path, **kwargs):
    times = kwargs.get('times', None)
    transmission_times = kwargs.get('transmission_times', None)
    costs = kwargs.get('costs', None)
    check_bpmn_bool = kwargs.get('check_bpmn', True)
    cost_types = kwargs.get('cost_types', None)
    
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
    
    wf_spec = BpmnSerializer().deserialize_workflow_spec(package)
    
    if check_bpmn_bool:
        check_bpmn(wf_spec)
    
    if times and transmission_times:
        add_times(wf_spec, times, transmission_times)
        
    if costs:
        add_costs(wf_spec, costs, cost_types)
    
    return wf_spec


def check_bpmn(wf_spec):
    desk_works = [task for task in wf_spec.task_specs.values() if get_type(task) == 'desk work']
    
    for desk_work in desk_works:
        # exactly one parallel gate input
        if not (len(desk_work.inputs) == 1 and type(desk_work.inputs[0]).__name__ in ['ParallelGateway', 'StartEvent']):
            raise WorkflowException(wf_spec, f'Desk work task {desk_work.name} does not have a single ParallelGate or StartEvent input')
            
        # exactly one parallel gate output
        if not (len(desk_work.outputs) == 1 and type(desk_work.outputs[0]).__name__ in ['ParallelGateway', 'EndEvent']):
            raise WorkflowException(wf_spec, f'Desk work task {desk_work.name} does not have a single ParallelGate or EndEvent output')
        
        # check digital inputs
        digital_inputs = [p for p in desk_work.inputs[0].inputs if get_type(p) == 'digital info']
        
        for digital_input in digital_inputs:
            #each digital information is on the same lane as the task itself
            if not digital_input.lane == desk_work.lane:
                print(f'WARNING: digital info {digital_input.name} is not in the same lane as the following task {desk_work.name}')
            
            #each digital information has exactly one precedessor in the flow (with possible intermediate nodes like parallel gateways),
            #which is called the same way as the information itself
            if not (len(digital_input.inputs) == 1):
                raise WorkflowException(wf_spec, f'Digital info {digital_input.name} has multiple inputs')
            preceding_desk_work = trace_back(digital_input.inputs[0], digital_input.description)
            if preceding_desk_work == None:
                continue
            if preceding_desk_work.lane == '':
                print(f'WARNING: preceding desk_work_task for node {desk_work.name} {preceding_desk_work.name} does not have a specified partner')



# helper function finding source of information
def trace_back(node, original_desc):
    if not len(node.inputs) == 1:
        raise WorkflowException(f'Error: {node.name} has multiple inputs; tracing back from {original_desc}')
    
    if type(node).__name__ == 'StartEvent':
        return None
    
    if type(node).__name__ in ['Simple', 'NoneTask']:
        if get_type(node) == 'desk work':
            raise WorkflowException(f'Error: reached desk work task {node.name} before finding information {original_desc}')
        elif get_type(node) == 'digital info':
            if not node.description == original_desc:
                print(f'WARNING: Digital Info {original_desc} is originating from other kind of information {node.description} @ {node.name}')
        else:
            print(f'WARNING: Digital Info {original_desc} is originating from other kind of task {node.description} @ {node.name}')
        return node
            
    if not type(node).__name__ == 'ParallelGateway':
        print(f'WARNING: tracing back digital info {original_desc} lead to unknown kind of node {node.name}')
        return node
    
    return trace_back(node.inputs[0], original_desc)


def add_times(wf_spec, times, transmission_times, mode='type'):
    if mode == 'type':
        for task_spec in wf_spec.task_specs.values():        
            ty = get_type(task_spec)
        
            if ty == 'digital info':
                # transmission time must not be added, if the node is used as input node for a task, but only as an actual transmission between two different tasks
                if get_type(task_spec.outputs[0].outputs[0]) == 'desk work':
                    continue
            
            if (not ty == '') and not (ty in times and ty in transmission_times):
                print(f'WARNING: Category {ty} is not known to either times or transmission_times')
        
            task_spec.data['time'] = times.get(ty, (1e-5, 0))
            task_spec.data['transmission_time'] = transmission_times.get(ty, (1e-5, 0))
    
    if mode == 'exact':
        for task_spec in wf_spec.task_specs.values():
            task_spec.data['time'] = times.get(task_spec.description, (1e-5, 0))
            task_spec.data['transmission_time'] = transmission_times.get(task_spec.description, (1e-5, 0))
    
    
def add_costs(wf_spec, costs, cost_types, mode='type'):
    no_costs = {}
    for cost_type in cost_types:
        no_costs[cost_type] = (0, 0)
    
    if mode == 'exact':
        for task_spec in wf_spec.task_specs.values():
            task_spec.data['cost'] = costs.get(task_spec.description, no_costs)
    
    elif mode == 'type':
        for task_spec in wf_spec.task_specs.values():
            ty = get_type(task_spec)

            if (not ty == '') and not (ty in costs):
                print(f'WARNING: Category {ty} is not known to either times or transmission_times')
            
            task_spec.data['cost'] = costs.get(ty, no_costs)

def get_type(task_spec):
    if (task_spec.description == None or task_spec.description.find('[') == -1):
        return ''

    return task_spec.description[task_spec.description.find('['):].replace('[', '').replace(']', '').lower()