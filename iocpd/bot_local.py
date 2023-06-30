# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 09:50:03 2022

@author: GarlefHupfer
"""
import os
import asyncio
import pandas
from .datamodel.crawler_local import Crawler
from .util.check import get_updates
from .processmining.miner import Miner
#from Visualizer.visualize import visualize
from .simulations.runner import Runner

class Bot():
    def __init__(self, project_path, **kwargs):
        # initializing the project, loading the data
        self.project_path = project_path
        self.event_log = pandas.DataFrame(columns=['process', 'key', 'from', 'to', 'timestamp'])
        self.next_activities = pandas.DataFrame(columns=['process', 'until', 'relevance', 'started', 'starttime'])
        self.processes = pandas.DataFrame(columns=['process', 'processtmstp', 'statustmstp', 'isfinished', 'resdescription', 'processauthor', 'processname', 
                                                   'endtime', 'isstarted', 'starttime', 'case:concept:name'])
        self.load_data()
        
        # base variables, mostly irrelevant for local testing
        self.update_time = kwargs.get('update_time') or 1
        self.cost_types= kwargs.get('cost_types') or ['material', 'personal', 'transport', 'vertrieb', 'equipment']
        self.bpmn_path = kwargs.get('bpmn_path') or None
        self.runner_config_path = kwargs.get('runner_config_path') or None
        self.log_path = kwargs.get('log_path') or None
        
        # initialize all helping objects
        self.crawler = Crawler(kwargs.get('local_processes_path') or self.project_path + 'processes/', self.processes) # used for local testing
        self.runner = Runner(project_path=self.project_path, bpmn_path=self.bpmn_path, config_path=self.runner_config_path, current_processes=self.processes,
                             times=kwargs.get('times'), transmission_times=kwargs.get('transmission_times'), costs=kwargs.get('costs'), cost_types=self.cost_types)
        self.miner = Miner(project_path=self.project_path, log_path=self.log_path, bpmn_path=self.bpmn_path, cost_types=self.cost_types)
        
        # initalizing local variables for the bot
        self.runner_update = True
        self.prognosis = None
        self.updates = {}
        
    
    def load_data(self):
        if os.path.exists(self.project_path + 'event_log.csv'):
            self.event_log = pandas.read_csv(self.project_path + 'event_log.csv')
            
        if os.path.exists(self.project_path + 'next_activities.csv'):
            self.next_activities = pandas.read_csv(self.project_path + 'next_activities.csv')
        
        if os.path.exists(self.project_path + 'processes.csv'):
            self.processes = pandas.read_csv(self.project_path + 'processes.csv')
    
    def save_data(self):
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        if not os.path.exists(self.project_path + 'temp'):
            os.mkdir(self.project_path + 'temp')
            
        asyncio.ensure_future(self.save_event_log())
        asyncio.ensure_future(self.save_next_activities())
        asyncio.ensure_future(self.save_processes())
        asyncio.ensure_future(self.save_duration())
        asyncio.ensure_future(self.save_costs())
        asyncio.ensure_future(self.save_petri_net())
        
    async def save_event_log(self):
        try:
            self.event_log.to_csv(self.project_path + 'event_log.csv', index=False)
        except:
            print('WARNING: Couldnt save event log')
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_event_log())
    
    async def save_next_activities(self):
        try:
            self.next_activities.to_csv(self.project_path + 'next_activities.csv', index=False)
        except:
            print('WARNING: Couldnt save next activities') 
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_next_activities())
        
    async def save_processes(self):
        try:
            self.processes.to_csv(self.project_path + 'processes.csv', index=False)
        except:
            print('WARNING: Couldnt save processes')
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_processes())
    
    async def save_duration(self):
        if self.prognosis == None:
            return
        
        try:
            with open(self.project_path + 'temp/duration.csv', 'w+') as f:
                for t in self.prognosis[0]:
                    f.write(f'{t}\n')
        except:
            print('WARNING: Couldnt save prognosis')
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_duration())
    
    async def save_costs(self):
        if self.prognosis == None:
            return
        
        try:
            self.prognosis[1].to_csv(self.project_path + 'temp/costs.csv', index=True)
        except:
            print('WARNING: Couldnt save cost prognosis')
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_costs())
            
    async def save_petri_net(self):
        try:
            self.miner.save_petri_net(self.project_path + 'temp/petri_net.pnml')
        except:
            print('WARNING: Couldnt save petri net')
            await asyncio.sleep(1)
            asyncio.ensure_future(self.save_petri_net())
    
    def start(self):
        self.crawler.start_crawling()
        asyncio.ensure_future(self.update())
        asyncio.ensure_future(self.update_runner())
    
    def stop(self):
        self.cancel_coro('update')
        self.cancel_coro('crawl')
        self.cancel_coro('update_runner')
        
    
    def cancel_coro(self, coro):
        loop = asyncio.get_running_loop()
        for tsk in asyncio.all_tasks(loop):
            if tsk._coro.__name__ == coro:
                tsk.cancel()

    
    async def update(self):
        if self.crawler.updated:
            if not type(self.processes).__name__ == 'NoneType':
                self.runner_update = True
                event_log_add = get_updates(self.processes, self.crawler.processes)
                self.event_log = pandas.concat([self.event_log, event_log_add], ignore_index=True, axis=0)
                
            self.processes = self.crawler.processes
                
            self.save_data()
            self.crawler.updated = False
        
        await asyncio.sleep(self.update_time)
        asyncio.ensure_future(self.update())
    
    async def update_runner(self):
        if self.runner_update:
            if not type(self.processes).__name__ == "NoneType":
                self.runner.update_processes(self.processes)
            self.next_activities = self.runner.get_next_activities_with_relevance()
            self.prognosis = self.runner.get_prognosis(self.processes)                
            
            self.save_data()
            self.runner_update = False
             
        await asyncio.sleep(self.update_time)
        asyncio.ensure_future(self.update_runner())
    
    def finish_project(self, force=False, project_id=None):
        self.runner.update_processes(self.processes)
        if not self.runner.wf.is_completed() and not force:
            print('WARNING: Project is not complete. If you still want to finish the project, please use force=True')
        
        if project_id == None:
            project_id = 1
            with open(self.log_path, 'r') as f:    
                for l in f.lines():
                    if l[:l.find('|')] == project_id:
                        project_id += 1
        
        with open(self.log_path, 'a') as f:
            for index, row in self.processes.iterrows():
                f.write(f'{project_id}|{row["processname"]}|{row["starttime"]}|{row["endtime"]}|{row["resources"]}|')
