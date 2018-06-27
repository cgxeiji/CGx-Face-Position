class Smoother:
    def __init__(self, size=3):
        self.size = size
        self.buffer = [0] * self.size

    def input(self, value):
        self.buffer.append(value)
        self.buffer.pop(0)

    def set(self, value):
        self.buffer = []
        for i in range(self.size):
            self.buffer.append(value)

    def value(self):
        return sum(self.buffer) / len(self.buffer)