from smoother import Smoother

class Eye:
    def __init__(self):
        self.x = Smoother(5)
        self.y = Smoother(5)

    def input(self, (x, y)):
        self.x.input(x)
        self.y.input(y)

    def set(self, (x, y)):
        self.x.set(x)
        self.y.set(y)

    def position(self):
        return (self.x.value(),self.y.value())
