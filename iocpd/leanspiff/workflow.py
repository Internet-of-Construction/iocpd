# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 19:16:00 2021

@author: GarlefHupfer
"""

from SpiffWorkflow.exceptions import WorkflowException
from .task import Task


class Workflow(object):
    def __init__(self, workflow_spec, **kwargs):
        assert workflow_spec is not None
        self.spec = workflow_spec
        
        # create an instance of every task
        self.tasks = []
        
        for task_spec in list(self.spec.task_specs.values()):
            Task(self, task_spec)
        
        
        #connect the tasks
        for t in self.tasks:
            for c in t.task_spec.outputs:
                t.children.append(self.get_task_by_task_spec(c))
            
            for p in t.task_spec.inputs:
                t.parents.append(self.get_task_by_task_spec(p))
        
        # get start in list of tasks
        for t in self.tasks:
            if t.task_spec == self.spec.start:
                self.start = t
                t.complete()
                break
           
    def get_task_by_task_id(self, task_id):
        for t in self.tasks:
            if t.id == task_id:
                return t
        
        msg = 'A task with the given task id (%s) was not found' % (task_id)
        raise WorkflowException(self.spec, msg)
        
    
    def get_task_by_task_spec(self, task_spec):
        for t in self.tasks:
            if t.task_spec == task_spec:
                return t
        
        msg = 'A task with the given task_spec (%s) was not found' % (task_spec)
        raise WorkflowException(self.spec, msg)
    
    
    def get_tasks(self, state=Task.ANY_MASK):
        return [t for t in self.tasks if t.state & state > 0]
        
    
    def is_completed(self):
        """
        Returns True if the entire Workflow is completed, False otherwise.

        :rtype: bool
        :return: Whether the workflow is completed.
        """
        for t in self.tasks:
            if t.state < Task.COMPLETED:
                return False
        
        return True
    
    
    def complete_task_from_id(self, task_id, force_prior=False, completion_time=None):
        #print('completing task ' + task_id)
        if task_id is None:
            raise WorkflowException(self.spec, 'task_id is None')
        task = self.get_task_by_task_id(task_id)
        if task == None:
            msg = 'A task with the given task_id (%s) was not found' % task_id
            raise WorkflowException(self.spec, msg)
        if task.state == Task.COMPLETED:
            return
        task.complete()
        if not completion_time==None:
            task.completion_time = completion_time
            task.transmitted_time = completion_time
        if force_prior:
            for p in self.get_task_by_task_id(task_id).parents:
                self.complete_task_from_id(p.id, force_prior, completion_time=completion_time)
        return
    
    
    def get_dump(self):
        """
        Returns a complete dump of the current internal task tree for
        debugging.

        :rtype:  str
        :returns: The debug information.
        """
        return self.start.get_dump()


    def dump(self):
        """
        Like :meth:`get_dump`, but prints the output to the terminal instead
        of returning it.
        """
        print(self.start.dump())