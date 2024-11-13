import websockets
import asyncio
import socket
import json

from src.libs.shared_memory import SharedMemory
from src.libs.median_filter import MedianFilter
import logging

class WebsocketClient():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem

        self.host = self.shmem.read_data("ws_host")
        self.port = self.shmem.read_data("ws_port")
        
        self.url = f"ws://{self.host}:{self.port}"

        self.reply_timeout = self.shmem.read_data("ws_reply")
        self.ping_timeout = self.shmem.read_data("ws_ping")
        self.sleep_time = self.shmem.read_data("ws_sleep")

        # server param
        self.is_connection = True

        # utils
        self.median_filter = MedianFilter(9)

        self.headers = [
            "is_tracking", 
            "is_autopilot", 
            "target_roi", 
            "error_px", 
            "new_course", 
            "altitude", 
            "airspeed", 
            "groundspeed", 
            "heading", 
            "vertical_speed", 
            "ground_distance",
            "flight_mode",
            "throttle",
            "arm_status",
        ]

    def handle_error(self):
        self.is_connection = False
        self.shmem.write_data("is_server_connection", self.is_connection)

    def handle_reply(self, data: str):
        self.is_connection = True
        self.shmem.write_data("is_server_connection", self.is_connection)
        try:
            msg: dict = json.loads(data)
            for name in self.headers:
                self.shmem.write_data(name, msg.get(name))
        except:
            return
        
    def create_request(self):
        msg = dict()
        is_no_msg = True

        init_roi = self.shmem.read_data("init_roi")
        roi_size = self.shmem.read_data("roi_size")
        is_retarget = self.shmem.read_data("is_retarget")
        new_flight_mode = self.shmem.read_data("new_flight_mode")

        if init_roi != None and roi_size:
            msg["init_roi"] = init_roi
            msg["roi_size"] = roi_size
            is_no_msg = False

        if is_retarget != None and roi_size:
            msg["is_retarget"] = is_retarget
            msg["roi_size"] = roi_size
            is_no_msg = False

        if new_flight_mode != None:
            msg["new_flight_mode"] = new_flight_mode
            is_no_msg = False

        if is_no_msg:
            return None
        
        # clear data
        self.shmem.write_data("init_roi")
        self.shmem.write_data("roi_size")
        self.shmem.write_data("is_retarget")
        self.shmem.write_data("new_flight_mode")

        return json.dumps(msg)

    async def start(self):
        while True:
            logging.debug('Creating new connection...')
            try:
                async for ws in websockets.connect(self.url):
                    while True:
                        try:
                            reply = await asyncio.wait_for(ws.recv(), timeout=self.reply_timeout)
                            self.handle_reply(reply)
                            msg = self.create_request()
                            if msg: 
                                await asyncio.wait_for(ws.send(msg), timeout=self.reply_timeout)
                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                            try:
                                self.handle_error()
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=self.ping_timeout)
                                logging.debug('Ping OK, keeping connection alive...')
                                continue
                            except:
                                logging.debug('Ping error - retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                                await asyncio.sleep(self.sleep_time)
                                break
                        logging.debug('Server said > {}'.format(reply))
            except socket.gaierror:
                logging.debug('Socket error - retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                await asyncio.sleep(self.sleep_time)
                continue
            except ConnectionRefusedError:
                logging.debug('Nobody seems to listen to this endpoint. Please check the URL.')
                logging.debug('Retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                await asyncio.sleep(self.sleep_time)
                continue

def start_client(ws_client: WebsocketClient):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_client.start())
