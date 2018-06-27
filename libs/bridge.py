from __future__ import print_function
import ConfigParser
import logging
import threading
from pose_sphere import PoseSphere

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
        self.poses = []
        self.robot = robot
        self.default = None

        self.load_poses()
        self.load_actions()
        

    def load_poses(self):
        config = ConfigParser.ConfigParser()
        config.read('config/poses.ini')
        for section in config.sections():
            priority = config.getint(section, 'priority')

            pose = PoseSphere(section, priority)

            pos = (config.getfloat(section, 'x'), config.getfloat(section, 'y'), config.getfloat(section, 'z'))
            a = config.getfloat(section, 'angle')
            tol = config.getfloat(section, 'tolerance')
            _type = config.get(section, 'type')

            if _type == 'Sphere':
                rad = config.getfloat(section, 'radius')
                pose.set_sphere(pos, a, rad, tol)
            elif _type == 'Block':
                p2 = (config.getfloat(section, 'x2'), config.getfloat(section, 'y2'), config.getfloat(section, 'z2'))
                pose.set_block(pos, p2, a, tol)

            timer = config.getfloat(section, 'time')
            action = config.get(section, 'action')
            pose.set_action(action, timer)

            if section == 'Pose Safe':
                self.default = pose

            self.poses.append(pose)

        self.poses.sort(key=lambda x: x.priority, reverse = True)
        
        for pose in self.poses:
            msg = ''
            if pose.type == 'sphere':
                msg = "Pose: '{}'[{}]({}) @ [{}]({}) with rad[{}] tol[{}] do '{}' in [{}s]".format(pose.name, pose.priority, pose.type, pose.position, pose.angle, pose.radius, pose.tolerance, pose.action, pose.timer)
            elif pose.type == 'block':
                msg = "Pose: '{}'[{}]({}) @ [{}][{}]({}) with tol[{}] do '{}' in [{}s]".format(pose.name, pose.priority, pose.type, pose.position,pose.p2, pose.angle, pose.tolerance, pose.action, pose.timer)
            logging.info(msg)
            print(msg)

    def load_actions(self):
        config = ConfigParser.ConfigParser()
        config.read('config/monitor.ini')
        for section in config.sections():
            pos = (config.getfloat(section, 'x'), config.getfloat(section, 'y'), config.getfloat(section, 'z'))
            rot = (config.getfloat(section, 'a'), config.getfloat(section, 'b'), config.getfloat(section, 'c'))
            tspeed = config.getfloat(section, 'tspeed')
            aspeed = config.getfloat(section, 'aspeed')
            
            action = _Action(section, pos, rot, tspeed, aspeed)

            self.actions.append(action)

        for action in self.actions:
            logging.info("Action: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))
            print("Action: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))

    def eval(self, position, angle):
        pose_name = ''
        pose_time = 0
        in_pose = False
        for pose in self.poses:
            if in_pose:
                pose.skip()
            elif pose.check(position, angle):
                pose_name = pose.name
                pose_time = pose.get_time()
                if pose.timeout():
                    self.do_action(self.default.action)
                    threading.Timer(2.0, self.do_action, args=[pose.action]).start()
                in_pose = True

        return pose_name, pose_time



    def do_action(self, action_name):
        for action in self.actions:
            if action.name == action_name:
                self.robot.set_translation_speed(action.tspeed)
                self.robot.set_rotation_speed(action.aspeed)
                self.robot.move(action.position, action.rotation)
                print("Doing {} as robot.move({}, {})".format(action.name, action.position, action.rotation))
                break
