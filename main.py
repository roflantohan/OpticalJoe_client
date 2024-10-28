from multiprocessing import Process, Manager
from src.websocket_client import WebsocketClient
from src.gui import TrackerAppGUI
import asyncio

if __name__ == "__main__":
    manager = Manager()
    shared_dict = manager.dict()

    ws_module = WebsocketClient(shared_dict)
    gui_module = TrackerAppGUI(shared_dict)
    
    p = Process(target=gui_module.start)
    p.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_module.start())

    p.terminate()
    # p.join()
