import json
import logging
from src.libs.shared_memory import SharedMemory

class ConfigLoader():
    
    def __init__(self, file_name, shmem: SharedMemory):
        self.shmem = shmem
        
        self.file_name = file_name
        self.config: dict = {}
        self.env = "dev"

    def read_config_file(self):
        try:
            with open(self.file_name) as config_file:
                self.config = json.load(config_file)
                logging.debug(f"CONFIG: Success reading {self.file_name}")
        except Exception as err:
            logging.error(f"(CONFIG) Error reading {self.file_name}: {err}")

    def load_env_config(self):
        self.env = self.config.get("env", "dev")
        self.env = self.env if self.env in ["dev", "prod"] else "dev"
        self.shmem.write_data("env", self.env)
        logging.debug(f"CONFIG: ENV mode -> {self.env}")

    def load_websocket_config(self):
        params: dict = self.config.get("websocket", {})
        env_params: dict = params.get(self.env, {})

        host = env_params.get("host", None)
        self.shmem.write_data("ws_host", host)

        port = env_params.get("port", None)
        self.shmem.write_data("ws_port", port)

        reply = env_params.get("reply_timeout", None)
        self.shmem.write_data("ws_reply", reply)

        ping = env_params.get("ping_timeout", None)
        self.shmem.write_data("ws_ping", ping)

        sleep = env_params.get("sleep_timeout", None)
        self.shmem.write_data("ws_sleep", sleep)

    def load_config(self):
        self.read_config_file()
        logging.info(f"CONFIG: start loading")
        self.load_env_config()
        self.load_websocket_config()
        logging.info(f"CONFIG: success loading")
