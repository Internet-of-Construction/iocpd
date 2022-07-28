# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 08:17:23 2022

@author: GarlefHupfer
"""

import asyncio
import websockets
import json
import logging
import datetime

class Crawler():
    def __init__(self, uri, endpoint, name, pw, database):
        self.uri = uri
        self.endpoint = endpoint
        self.name = name
        self.pw = pw
        self.database = database
        self.processes = ""
        self.updated = False
    
    
    async def start_crawling(self):
        print('starting to crawl in crawler')
        event_loop = asyncio.get_event_loop()
        
        try:
            event_loop.create_task(self.crawl())
        except Exception:
            print('Something wrong happened while the workload was running.')
            for task in asyncio.Task.all_tasks(loop=event_loop):
                task.cancel()
            raise
        
        print('started to crawl in crawler')
        
    
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
        
        async with websockets.connect(self.uri) as websocket:
            await self.send(websocket, connect_msg)
            return await self.send(websocket, get_processes_msg)


    async def send(self, websocket, msg):
        print(f">>> {msg[0:200]}")
        await websocket.send(msg)
        recv = await websocket.recv()
        print(f"<<< {recv[0:200]}")
        
        return recv
        
    
    async def crawl(self):
        print(f'[{datetime.datetime.now()}] getting processes')
        event_loop = asyncio.get_running_loop()
        try:
            task = event_loop.create_task(self.get_processes())
        except Exception:
            logging.info('Something wrong happened while the workload was running.')
            for task in asyncio.Task.all_tasks(loop=event_loop):
                task.cancel()
            raise
        
        while not task.done():
            await asyncio.sleep(1)
        
        processes = task.result()
            
        if not processes == self.processes:
            # processes are updated, check differences
            print(f'[{datetime.datetime.now()}] New processes, updating...')
            self.processes = processes
            self.updated = True
            
        print(f'[{datetime.datetime.now()}] waiting 60 seconds')
        await asyncio.sleep(60)
        print(f'[{datetime.datetime.now()}] rerunning coroutine')
        event_loop.create_task(self.start_crawling())