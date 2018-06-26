from __future__ import print_function
import math

class PoseSphere:
    def __init__(self, name):
        self.position = (0.0, 0.0, 0.0)
        self.angle = 0.0
        self.diameter = 1.0
        self.tolerance = 1.0
        self.name = name

    def set_sphere(self, (x, y, z), angle, diameter=5, tolerance=10):
        self.position = (x, y, z)
        self.angle = angle
        self.diameter = diameter
        self.tolerance = tolerance

    def check(self, (x, y, z), angle):
        distance = math.sqrt(math.pow(x - self.position[0], 2) + math.pow(y - self.position[1], 2) + math.pow(z - self.position[2], 2))
        delta_angle = abs(angle - self.angle)

        return (distance <= self.diameter) and (delta_angle < self.tolerance)

