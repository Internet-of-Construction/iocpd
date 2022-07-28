# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 08:17:23 2022

@author: GarlefHupfer
"""

import os
import asyncio
import pandas

#----------------------------------------------------------------------------
# temporary use for local testing
#----------------------------------------------------------------------------
class Crawler():
    def __init__(self, path, processes):
        self.path = path
        self.processes = processes
        self.updated = False
        
    def start_crawling(self):
        asyncio.ensure_future(self.crawl2())
    
    async def crawl2(self):
        task = asyncio.ensure_future(self.get_processes2())
        await task
        processes = task.result()
        
        if not type(processes).__name__ == 'NoneType':
            if not processes.equals(self.processes):
                #print(f'\n\n[{datetime.datetime.now()}] New processes, updating...')
                #processes.to_csv(self.safe_path + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S") + '.csv')
                self.processes = processes
                self.updated = True
        
        await asyncio.sleep(1)
        asyncio.ensure_future(self.crawl2())
    
    async def get_processes(self):
        files = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
        if not files:
            return
        flag = 0
        file = None
        for f in files:
            if int(f.replace('.csv', '')) > flag:
                file = f
                flag = int(f.replace('.csv', ''))
        
        processes = pandas.read_csv(self.path + file)
        return processes