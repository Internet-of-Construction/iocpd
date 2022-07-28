# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 09:50:03 2022

@author: GarlefHupfer
"""

import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')
import asyncio
import pandas
import ast
#import numpy as py
#import matplotlib.pyplot as plt
from Crawler.crawler import Crawler
from Crawler.crawler import Crawler2
from Checker.check import get_updates
from Miner.miner import Miner
#from Visualizer.visualize import visualize
from Runner.runner import Runner
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')


#TODOs:::
#- Gesamten Code durchgehen und Logik anhand eines Beispiels aufzeigen
#- Code bereinigen DONE
#- Heuristik für Zeitplanverschiebung
#- Svg mit Farben DONE
#- Gantt Chart zusätzlich DONE
#- Einzelne Akteure betrachten (highlighting erlauben) DONE
#- Label an die Prognose DONE
#- Prozesskosten einbauen: Material, Personal, Transport, Lohn, <Rüstung, Schalung und Verbau>, Vertrieb, Betrieb, Geräte
#- Event Log in Tabellenform DONE
#- for saving: create temp if not existant DONE
#- Next Activities: Add legend and coloring
#- Prognose restliche Dauer: In Daten umwandeln
#- Gantt Chart Coloring
#- costs and times: add different modes like exact name or type

class Bot():
    def __init__(self, project_path, **kwargs):
        # initializing the project, loading the data
        self.project_path = project_path
        self.event_log = pandas.DataFrame(columns=['process', 'key', 'from', 'to', 'timestamp'])
        self.next_activities = pandas.DataFrame(columns=['activity', 'until', 'relevance', 'started', 'starttime'])
        self.processes = pandas.DataFrame(columns=['process', 'processtmstp', 'statustmstp', 'isfinished', 'resdescription', 'processauthor', 'processname', 
                                                   'endtime', 'isstarted', 'starttime', 'case:concept:name'])
        self.load_data()
        
        # base variables, mostly irrelevant for local testing
        self.uri = kwargs.get('uri') or None
        self.endpoint = kwargs.get('endpoint') or None
        self.name = kwargs.get('name') or None
        self.pw = kwargs.get('pw') or None
        self.database = kwargs.get('database') or None
        self.update_time = kwargs.get('update_time') or 1
        self.cost_types= kwargs.get('cost_types') or ['material', 'personal', 'transport', 'vertrieb', 'equipment']
        self.bpmn_path = kwargs.get('bpmn_path') or None
        self.runner_config_path = kwargs.get('runner_config_path') or None
        self.log_path = kwargs.get('log_path') or None
        
        # initialize all helping objects
        #self.crawler = Crawler(uri = uri, endpoint = endpoint, name = name, pw = pw, database = database) # used for real data model
        self.crawler = Crawler2(kwargs.get('local_processes_path') or self.project_path + 'processes/', self.processes) # used for local testing
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
        
        
    def start2(self):
        self.crawler.start_crawling2()
        asyncio.ensure_future(self.update())
        asyncio.ensure_future(self.update_runner())
        
    def stop2(self):
        self.cancel_coro('update')
        self.cancel_coro('crawl2')
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
            
    
def __main__():
    project_path = 'testing/project2/'
    
    # parameters for ontology
    uri = "wss://server.ip.rwth-aachen.de:443/ioc/ws"
    endpoint = "https://server.ip.rwth-aachen.de/ioc/stardog"
    name = "Garlef Hupfer"
    pw = "9mZpkAsHtc"
    database = "IOC_IL"
    
    # parameter for local testing
    local_processes_path = project_path + 'processes_progress/'
    
    # parameters for running prognosis etc.
    bpmn_path = project_path + 'project.bpmn'
    runner_config_path = project_path + 'runner_config.cfg'
    
    log_path = project_path + 'log.csv'
    
    # times and costs
    times_path = project_path + 'times.cfg'
    transmission_times_path = project_path + 'transmission_times.cfg'
    
    with open(times_path) as f:
        data = f.read()
        f.close()
    times = ast.literal_eval(data)
    
    with open(transmission_times_path ) as f:
        data = f.read()
        f.close()
    transmission_times = ast.literal_eval(data)
    
    with open('Runner/res/costs.cfg') as f:
        data = f.read()
        f.close()
    costs = ast.literal_eval(data)
    
    bot = Bot(project_path=project_path, uri=uri, endpoint=endpoint, name=name, pw=pw, database=database,
              bpmn_path=bpmn_path, runner_config_path=runner_config_path, local_processes_path=local_processes_path, log_path=log_path, times=times, transmission_times=transmission_times,
              costs=costs)
    
    globals()['bot'] = bot
    #bot.stop2()
    #bot.start2()


__main__()
