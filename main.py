from multiprocessing import Process

from src.libs.shared_memory import SharedMemory
from src.libs.config_loader import ConfigLoader
from src.websocket import WebsocketClient
from src.gui import TrackerAppGUI

if __name__ == "__main__":
    shmem = SharedMemory()
    ConfigLoader("config.dev.json", shmem).load()

    ws_module = WebsocketClient(shmem)
    gui_module = TrackerAppGUI(shmem)
    
    p = Process(target=WebsocketClient(shmem).start)
    p.start()

    gui_module.start()

    p.terminate()
