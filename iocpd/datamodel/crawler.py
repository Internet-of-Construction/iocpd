# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 08:17:23 2022

@author: GarlefHupfer
"""

import asyncio
import websockets
import json
from ..util.reader import get_processes_from_json

class Crawler():
    def __init__(self, uri, endpoint, name, pw, database, processes):
        self.uri = uri
        self.endpoint = endpoint
        self.name = name
        self.pw = pw
        self.database = database
        self.processes = processes
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