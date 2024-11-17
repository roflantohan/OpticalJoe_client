import asyncio
from multiprocessing import Process

from src.libs.shared_memory import SharedMemory
from src.libs.config_loader import ConfigLoader
from src.websocket_client import WebsocketClient
from src.gui import TrackerAppGUI

def start_ws(ws_module):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_module.start())

if __name__ == "__main__":
    shmem = SharedMemory()

    config_module = ConfigLoader("config.json", shmem)
    config_module.load_config()

    ws_module = WebsocketClient(shmem)
    gui_module = TrackerAppGUI(shmem)
    
    p = Process(target=start_ws, args=(ws_module, ))
    p.start()

    gui_module.start()

    p.terminate()
