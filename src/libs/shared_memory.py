from multiprocessing.managers import DictProxy

class SharedMemory:
    def __init__(self, shared_dict: DictProxy):
        self.shared_dict = shared_dict

    def write_data(self, param, value = None):
        self.shared_dict[param] = value
    
    def read_data(self, param):
        return self.shared_dict.get(param)
