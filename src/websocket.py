import websockets
import asyncio
import json

from src.libs.shared_memory import SharedMemory

class WebsocketClient():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.host = self.shmem.read_config("ws_host")
        self.port = self.shmem.read_config("ws_port")
        self.reply_timeout = self.shmem.read_config("ws_reply")
        self.ping_timeout = self.shmem.read_config("ws_ping")
        self.sleep_time = self.shmem.read_config("ws_sleep")
        self.url = f"ws://{self.host}:{self.port}"

    def on_reply(self, data: str):
        try:
            msg: dict = json.loads(data)
            for name in self.shmem.headers:
                self.shmem.write_data(name, msg.get(name, None))
        except:
            return
        
    def on_request(self):
        msg = dict()

        init_roi = self.shmem.read_data("init_roi")
        roi_size = self.shmem.read_data("roi_size")
        is_retarget = self.shmem.read_data("is_retarget")
        new_flight_mode = self.shmem.read_data("new_flight_mode")

        if init_roi != None and roi_size:
            msg["init_roi"] = init_roi
            msg["roi_size"] = roi_size

        if is_retarget and roi_size:
            msg["is_retarget"] = is_retarget
            msg["roi_size"] = roi_size

        if new_flight_mode:
            msg["flight_mode"] = new_flight_mode

        self.shmem.write_data("init_roi")
        self.shmem.write_data("roi_size")
        self.shmem.write_data("is_retarget")
        self.shmem.write_data("new_flight_mode")

        return json.dumps(msg) if len(msg) else None

    async def listen(self):
        while True:
            try:
                async for ws in websockets.connect(self.url):
                    while True:
                        try:
                            reply = await asyncio.wait_for(ws.recv(), timeout=self.reply_timeout)
                            self.on_reply(reply)
                            msg = self.on_request()
                            if not msg: continue
                            await asyncio.wait_for(ws.send(msg), timeout=self.reply_timeout)
                        except:
                            await asyncio.wait_for(ws.ping(), timeout=self.ping_timeout)
            except:
                await asyncio.sleep(self.sleep_time)
                continue

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.listen())
