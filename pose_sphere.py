from __future__ import print_function
import math
import time

class PoseSphere:
    def __init__(self, name):
        self.position = (0.0, 0.0, 0.0)
        self.angle = 0.0
        self.diameter = 1.0
        self.tolerance = 1.0
        self.name = name
        self.time_check = None
        self.timer = 0
        self.action = ''

    def set_sphere(self, (x, y, z), angle, diameter=5, tolerance=10):
        self.position = (x, y, z)
        self.angle = angle
        self.diameter = diameter
        self.tolerance = tolerance

    def set_action(self, action, time):
        self.action = action
        self.timer = time

    def check(self, (x, y, z), angle):
        distance = math.sqrt(math.pow(x - self.position[0], 2) + math.pow(y - self.position[1], 2) + math.pow(z - self.position[2], 2))
        delta_angle = abs(angle - self.angle)

        if (distance <= self.diameter) and (delta_angle < self.tolerance):
            if self.time_check == None:
                self.time_check = time.time()
            return True

        self.time_check = None
        return False

    def get_time(self):
        if self.time_check != None:
            return time.time() - self.time_check
        else:
            return 0.0

    def timeout(self):
        if self.timer != 0:
            if self.get_time() >= self.timer:
                return True

        return False

