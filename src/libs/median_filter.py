import collections

class MedianFilter:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.values = collections.deque(maxlen=window_size)

    def update(self, new_value):
        self.values.append(new_value)
        return sorted(self.values)[len(self.values) // 2]
