import asyncio
import websockets
import json

async def send(websocket, msg): 
    print(f">>> {msg}")
    await websocket.send(msg)
    recv = await websocket.recv()
    print(f"<<< {recv}")
    
    return recv


async def main():
    uri = "wss://server.ip.rwth-aachen.de:443/ioc/ws"
    name = "Garlef Hupfer"
    pw = "9mZpkAsHtc"
    
    async with websockets.connect(uri, max_size=100*1048576, ping_interval=None) as websocket:
        connect_msg = json.dumps({
            "header": {
                "name": name,
                "password": pw
                },
            "body": {
                "database": "IOC_IL",
                "endpoint": "http://ioc.rob.arch.rwth-aachen.de"
                }
            })
        
        await send(websocket, connect_msg)
        
        get_processes_msg = json.dumps({
            "header": {
                "name": "Garlef Hupfer",
                "password": "9mZpkAsHtc"
                },
            "body": {
                "req": "getProcessLogs"
                }
            })
        
        processes = await send(websocket, get_processes_msg)
        
        with open('processes.json', 'w') as file:
            file.write(processes)
            file.close()
        
        
        globals()['processes'] = processes



# run asyncio
try:
    loop = asyncio.get_running_loop()
except RuntimeError:  # 'RuntimeError: There is no current event loop...'
    loop = None

if loop and loop.is_running():
    print('Async event loop already running. Adding coroutine to the event loop.')
    tsk = loop.create_task(main())
    # ^-- https://docs.python.org/3/library/asyncio-task.html#task-object
    # Optionally, a callback function can be executed when the coroutine completes
    
    tsk.add_done_callback(
        lambda t: print(f'Task done with result={t.result()}  << return val of main()'))
else:
    print('Starting new event loop')
    asyncio.run(main())