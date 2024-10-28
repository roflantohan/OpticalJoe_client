from multiprocessing.managers import DictProxy
import websockets
import asyncio
import socket
import json

from src.libs.shared_memory import SharedMemory
from src.libs.median_filter import MedianFilter
import logging

logger = logging.getLogger(__name__)

# logging.basicConfig(
#     stream=sys.stdout,
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )


class WebsocketClient(SharedMemory):
    def __init__(self, shared_dict: DictProxy):
        super().__init__(shared_dict)

        self.url = "ws://0.0.0.0:3030"

        # set some default values
        self.reply_timeout = 10
        self.ping_timeout = 5
        self.sleep_time = 1

        # server param
        self.is_connection = True

        # utils
        self.median_filter = MedianFilter(9)

    def handle_error(self):
        self.is_connection = False
        self.write_data("is_server_connection", self.is_connection)

    def handle_reply(self, data: str):
        self.is_connection = True
        self.write_data("is_server_connection", self.is_connection)
        try:
            msg: dict = json.loads(data)
            headers = ["is_tracking", "is_autopilot", "target_roi", "error_px", "new_course", "altitude", "airspeed", "groundspeed", "heading", "vertical_speed", "ground_distance"]
            for name in headers:
                self.write_data(name, msg.get(name))
        except:
            return
        
    def create_request(self):
        msg = dict()
        is_no_msg = True

        init_roi = self.read_data("init_roi")
        roi_size = self.read_data("roi_size")
        is_retarget = self.read_data("is_retarget")
        is_autopilot = self.read_data("new_is_autopilot")

        if init_roi != None and roi_size:
            msg["init_roi"] = init_roi
            msg["roi_size"] = roi_size
            is_no_msg = False

        if is_retarget != None and roi_size:
            msg["is_retarget"] = is_retarget
            msg["roi_size"] = roi_size
            is_no_msg = False

        if is_autopilot != None:
            msg["is_autopilot"] = is_autopilot
            is_no_msg = False

        if is_no_msg:
            return None
        
        # clear data
        self.write_data("init_roi")
        self.write_data("roi_size")
        self.write_data("is_retarget")
        self.write_data("new_is_autopilot")

        return json.dumps(msg)

    async def start(self):
        while True:
            logger.debug('Creating new connection...')
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
                                logger.debug('Ping OK, keeping connection alive...')
                                continue
                            except:
                                logger.debug('Ping error - retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                                await asyncio.sleep(self.sleep_time)
                                break
                        logger.debug('Server said > {}'.format(reply))
            except socket.gaierror:
                logger.debug('Socket error - retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                await asyncio.sleep(self.sleep_time)
                continue
            except ConnectionRefusedError:
                logger.debug('Nobody seems to listen to this endpoint. Please check the URL.')
                logger.debug('Retrying connection in {} sec (Ctrl-C to quit)'.format(self.sleep_time))
                await asyncio.sleep(self.sleep_time)
                continue

def start_client(ws_client: WebsocketClient):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_client.start())
