# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 19:12:51 2021

@author: GarlefHupfer
"""

from SpiffWorkflow.exceptions import WorkflowException
import numpy as py
from datetime import timedelta

class Task(object):
    FUTURE = 1
    READY = 2
    COMPLETED = 4
    CANCELLED = 8
    
    ANY_MASK = FUTURE | READY | COMPLETED | CANCELLED
    
    def __init__(self, workflow, task_spec, state=FUTURE):
        """
        Constructor.
        """
        assert workflow is not None
        assert task_spec is not None
        self.workflow = workflow
        self.parents = []
        self.children = []
        self.state = state
        self.task_spec = task_spec
        self.time = task_spec.data.get('time', (1e-5, 0))
        self.transmission_time = task_spec.data.get('transmission_time', (1e-5, 0))
        self.id = self.task_spec.name
        self.workflow.tasks.append(self)
        

    def get_type(self):
        if (self.task_spec.description == None):
            return 'Unknown'
        if (self.task_spec.description.find('[') == -1):
            return 'placeholder'
        
        return self.task_spec.description[self.task_spec.description.find('['):].replace('[', '').replace(']', '').lower()
    
    
    def get_time(self):
        return timedelta(hours=py.random.normal(self.time[0], self.time[1]))
    
    
    def get_transmission_time(self):
        return timedelta(hours=py.random.normal(self.transmission_time[0], self.transmission_time[1]))
    
    
    def get_costs(self):
        costs = self.task_spec.data.get('cost', {})
        cost_types = list(costs.keys())
        actual_costs = {}
        for cost_type in cost_types:
            actual_costs[cost_type] = py.random.normal(costs[cost_type][0], costs[cost_type][1])
        return actual_costs
    
    
    def _update_state(self):
        if self.state >= 2:
            return
        
        ready = True
        
        for c in self.parents:
            if c.state < self.COMPLETED:
                ready = False
                break
        
        if ready:
            self.set_state(self.READY)
    
    
    def get_state(self):
        return self.state
    
    
    def set_state(self, value, force=False):
        """
        Setting force to True allows for changing a state after it
        COMPLETED. This would otherwise be invalid.
        """
        if self.state == value:
            return
        if value < self.state and not force:
            raise WorkflowException(self.task_spec, 'illegal transition of states')
            
        self.state = value
    
    
    def is_completed(self):
        return self.state == self.COMPLETED
    
    
    def get_name(self):
        return str(self.task_spec.name)


    def get_description(self):
        return str(self.task_spec.description)
    
    def complete(self):
        self.set_state(self.COMPLETED)
        
        for c in self.children:
            c._update_state()
    
    def unfinish(self):
        if self.state <= self.FUTURE:
            return
        
        self.set_state(self.FUTURE, force=True)
        self._update_state()
        
        for c in self.children:
            c.unfinish()
    
    def get_inputs(self):
        # give back all direct inputs and such before a gateway
        inputs = []
        for parent_task in self.parents:
            inputs += self._get_inputs(parent_task)
        return inputs
    
    def _get_inputs(self, task):
        # helper function for above input search
        if type(task.task_spec).__name__ in ["ExclusiveGateway", "ParallelGateway"]:
            inputs = []
            for parent_task in task.parents:
                inputs += self._get_inputs(parent_task)
            return inputs
        if (task.get_type() in ['digital info', 'element', 'note', 'ressource', 'date']):
            return [task]
        return []
        
    def cancel(self):
        self.set_state(self.CANCELLED)
        
        for c in self.children:
            cancelled = True
            
            for p in c.parents:
                if p.state < self.CANCELLED:
                    cancelled = False
                
            if cancelled:
                c.cancel()
                    
    
    def get_dump(self, indent=0, recursive=True):
        """
        Returns the subtree as a string for debugging.

        :rtype:  str
        :returns: The debug information.
        """
        dbg = (' ' * indent * 2)
        dbg += '%s/' % self.id
        dbg += ' Task of %s' % self.get_name()
        if self.task_spec.description:
            dbg += ' (%s)' % self.get_description().replace('\n', '')
        dbg += ' State: %s' % str(self.state)
        dbg += ' Children: %s' % len(self.children)
        if recursive:
            for child in self.children:
                dbg += '\n' + child.get_dump(indent + 1)
        return dbg


    def dump(self, indent=0):
        """
        Prints the subtree as a string for debugging.
        """
        print(self.get_dump())