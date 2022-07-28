# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 08:17:23 2022

@author: GarlefHupfer
"""

import os
import asyncio
import websockets
import json
from Read.reader import get_processes_from_json
import pandas

class Crawler():
    def __init__(self, uri, endpoint, name, pw, database):
        self.uri = uri
        self.endpoint = endpoint
        self.name = name
        self.pw = pw
        self.database = database
        self.processes = None
        self.updated = False
    
    
    def start_crawling(self):
        asyncio.ensure_future(self.crawl())
        
    async def crawl(self):
        #print(f'[{datetime.datetime.now()}] getting processes')
        task = asyncio.ensure_future(self.get_processes())
        await task
        processes = get_processes_from_json(task.result())
        
        if not processes.equals(self.processes):
            #print(f'[{datetime.datetime.now()}] New processes, updating...')
            #processes.to_csv(self.safe_path + datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S") + '.csv')
            self.processes = processes
            self.updated = True
        
        await asyncio.sleep(60)
        asyncio.ensure_future(self.crawl())
    
    async def get_processes(self):
        connect_msg = json.dumps({
            "header": {
                "name": self.name,
                "password": self.pw
                },
            "body": {
                "database": self.database,
                "endpoint": self.endpoint
                }
            })
        
        get_processes_msg = json.dumps({
            "header": {
                "name": self.name,
                "password": self.pw
                },
            "body": {
                "req": "getProcessLogs"
                }
            })
        
        async with websockets.connect(self.uri, max_size=1024*1024*10) as websocket:
            await self.send(websocket, connect_msg)
            return await self.send(websocket, get_processes_msg)
        
    async def send(self, websocket, msg):
        print(f">>> {msg[0:200]}")
        await websocket.send(msg)
        recv = await websocket.recv()
        print(f"<<< {recv[0:200]}")
        return recv
    
    
#----------------------------------------------------------------------------
# temporary use for local testing
#----------------------------------------------------------------------------
class Crawler2():
    def __init__(self, path, processes):
        self.path = path
        self.processes = processes
        self.updated = False
        
    def start_crawling2(self):
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
    
    async def get_processes2(self):
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