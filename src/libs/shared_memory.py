from multiprocessing import Manager

class SharedMemory:
    def __init__(self):
        manager = Manager()
        self.shared = manager.dict()
        self.config = manager.dict()
        self.headers = [
            "is_tracking", 
            "target_roi", 
            "error", 
            "is_autopilot",
            "flight_mode",
            "course", 
            "altitude", 
            "heading", 
            "air_speed", 
            "ground_speed", 
            "vertical_speed", 
            "throttle_level",
        ]

    def write_config(self, param, value = None):
        self.config[param] = value

    def read_config(self, param):
        return self.config.get(param, None)

    def write_data(self, param, value = None):
        self.shared[param] = value
    
    def read_data(self, param):
        return self.shared.get(param, None)
