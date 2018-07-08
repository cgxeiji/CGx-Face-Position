from utils import Smoother


class Eye:
    def __init__(self):
        self.x = Smoother(2)
        self.y = Smoother(2)

    def input(self, (x, y)):
        self.x.input(x)
        self.y.input(y)

    def set(self, (x, y)):
        self.x.set(x)
        self.y.set(y)

    def position(self):
        return (self.x.value(), self.y.value())
