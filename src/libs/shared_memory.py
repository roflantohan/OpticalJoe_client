from multiprocessing import Manager

class SharedMemory:
    def __init__(self):
        manager = Manager()
        self.shared_dict = manager.dict()

    def write_data(self, param, value = None):
        self.shared_dict[param] = value
    
    def read_data(self, param):
        return self.shared_dict.get(param)
