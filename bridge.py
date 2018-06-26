from __future__ import print_function
import ConfigParser

class _Action:
    def __init__(self, name, (x, y, z), (a, b, c), tspeed, aspeed):
        self.name = name
        self.position = (x, y, z)
        self.rotation = (a, b, c)
        self.tspeed = tspeed
        self.aspeed = aspeed


class Bridge:
    def __init__(self, robot):
        self.actions = []
        self.robot = robot
        self.load()

    def load(self):
        config = ConfigParser.ConfigParser()
        config.read('monitor.ini')
        for section in config.sections():
            print(section)
            pos = (config.getfloat(section, 'x'), config.getfloat(section, 'y'), config.getfloat(section, 'z'))
            rot = (config.getfloat(section, 'a'), config.getfloat(section, 'b'), config.getfloat(section, 'c'))
            tspeed = config.getfloat(section, 'tspeed')
            aspeed = config.getfloat(section, 'aspeed')
            
            action = _Action(section, pos, rot, tspeed, aspeed)

            self.actions.append(action)

    def do_action(self, action_name):
        for action in self.actions:
            if action.name == action_name:
                self.robot.set_translation_speed(action.tspeed)
                self.robot.set_rotation_speed(action.aspeed)
                self.robot.move(action.position, action.rotation)
                print("Doing {} as robot.move({}, {})".format(action.name, action.position, action.rotation))
                break
