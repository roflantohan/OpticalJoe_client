import asyncio
from multiprocessing import Process

from src.libs.shared_memory import SharedMemory
from src.libs.config_loader import ConfigLoader
from src.websocket_client import WebsocketClient
from src.gui import TrackerAppGUI

if __name__ == "__main__":
    shmem = SharedMemory()

    config_module = ConfigLoader("config.json", shmem)
    config_module.load_config()

    ws_module = WebsocketClient(shmem)
    gui_module = TrackerAppGUI(shmem)
    
    p = Process(target=gui_module.start)
    p.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_module.start())

    p.terminate()
    p.join()
