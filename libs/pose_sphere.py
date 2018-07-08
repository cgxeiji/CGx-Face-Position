from __future__ import print_function

import math
import threading
import time


class PoseSphere:
    def __init__(self, name, priority=1):
        self.position = (0.0, 0.0, 0.0)
        self.p2 = (0.0, 0.0, 0.0)
        self.type = 'sphere'
        self.angle = 0.0
        self.radius = 1.0
        self.tolerance = 1.0
        self.name = name
        self.time_check = None
        self.timer = 0
        self.action = ''
        self.timeout_raised = False
        self.priority = priority

    def set_sphere(self, (x, y, z), angle, radius=5, tolerance=10):
        self.type = 'sphere'
        self.position = (x, y, z)
        self.angle = angle
        self.radius = radius
        self.tolerance = tolerance

    def set_block(self, (x1, y1, z1), (x2, y2, z2), angle, tolerance=10):
        self.type = 'block'
        self.position = (max([x1, x2]), max([y1, y2]), max([z1, z2]))
        self.p2 = (min([x1, x2]), min([y1, y2]), min([z1, z2]))
        self.angle = angle
        self.tolerance = tolerance

    def set_action(self, action, time):
        self.action = action
        self.timer = time

    def check(self, (x, y, z), angle):
        if self.type == 'sphere':
            distance = math.sqrt(math.pow(x - self.position[0], 2) + math.pow(
                y - self.position[1], 2) + math.pow(z - self.position[2], 2))
            delta_angle = abs(angle - self.angle)

            if (distance <= self.radius) and (delta_angle < self.tolerance):
                if self.time_check == None:
                    self.time_check = time.time()
                return True
        elif self.type == 'block':
            inside = (self.p2[0] <= x <= self.position[0]) and (
                self.p2[1] <= y <= self.position[1]) and (self.p2[2] <= z <= self.position[2])
            delta_angle = abs(angle - self.angle)

            if inside and (delta_angle < self.tolerance):
                if self.time_check == None:
                    self.time_check = time.time()
                return True

        self.time_check = None
        self.timeout_raised = False
        return False

    def get_time(self):
        if self.time_check != None:
            return time.time() - self.time_check
        else:
            return 0.0

    def timeout(self):
        if self.timer != 0:
            if self.get_time() >= self.timer and not self.timeout_raised:
                self.timeout_raised = True
                return True

        return False

    def skip(self):
        self.time_check = None
        self.timeout_raised = False
