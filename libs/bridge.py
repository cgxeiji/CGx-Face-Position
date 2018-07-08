from __future__ import print_function
import ConfigParser
import logging
import threading
import time
from pose_sphere import PoseSphere
from config_parser import get_config_variable as gcv

class _Action:
    def __init__(self, name, (x, y, z), (a, b, c), tspeed, aspeed):
        self.name = name
        self.position = (x, y, z)
        self.rotation = (a, b, c)
        self.tspeed = tspeed
        self.aspeed = aspeed
        self.exe_time = 0.0

class Bridge:
    def __init__(self, robot):
        self.actions = []
        self.poses = []
        self.animations = []
        self.robot = robot
        self.default = None

        self.current_zone = ''
        self.next_zone = ''
        self.current_timer = 0.0
        self.zone_timeout = gcv('zone timeout', 'float')
        self.outside_safe_timer = 0.0
        self.max_outside_safe_time = gcv('max outside safe time', 'float')

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

            if 'anim' in section:
                action.exe_time = config.getfloat(section, 'time')
                self.animations.append(action)
            
            self.actions.append(action)

        for action in self.actions:
            logging.info("Action: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))
            print("Action: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))
        for action in self.animations:
            logging.info("Animation: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))
            print("Animation: '{}' @ [{} -> {}][{} -> {}]".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))


    def eval(self, position, angle):
        pose_name = ''
        pose_time = 0
        in_pose = False
        for pose in self.poses:
            if in_pose:
                pose.skip()
            elif pose.check(position, angle):
                if pose.name != self.current_zone and self.current_zone != '':
                    if pose.name != self.next_zone:
                        self.current_timer = time.time()
                        self.next_zone = pose.name
                    pose_name = self.current_zone
                    pose_time = -1.0
                    if time.time() - self.current_timer < self.zone_timeout:
                        in_pose = True
                        continue
                pose_name = pose.name
                pose_time = pose.get_time()
                self.next_zone = ''
                if (self.current_zone not in pose_name) and (pose_name not in 'Pose Safe') and (self.current_zone not in 'Pose Safe'):
                    if self.outside_safe_timer == 0.0:
                        self.outside_safe_timer = time.time()
                    self.do_action(pose.action) # Do the next action directly if the user changes posture from bad posture to bad posture and skips good posture
                if pose.timeout():
                    if 'anim' in pose.action:
                        threading.Timer(0.1, self.do_animation).start()
                    else:
                        if pose_name in 'Pose Safe':
                            if self.outside_safe_timer != 0.0:
                                if time.time() - self.outside_safe_timer > self.max_outside_safe_time:
                                    self.do_action('Default Fast')
                                else:
                                    self.do_action(pose.action)
                            self.outside_safe_timer = 0.0
                        else:
                            self.do_action(pose.action)
                in_pose = True
                self.current_zone = pose_name
        if pose_name == '':
            self.current_zone = ''
        return pose_name, pose_time

    def restart_zone_timers(self):
        for pose in self.poses:
            pose.skip()

    def do_action(self, action_name):
        for action in self.actions:
            if action.name == action_name:
                self.robot.set_translation_speed(action.tspeed)
                self.robot.set_rotation_speed(action.aspeed)
                self.robot.move(action.position, action.rotation)
                logging.info("motion->{}".format(action_name))
                print("Doing {} as robot.move({} -> {}, {} -> {})".format(action.name, action.position, action.tspeed, action.rotation, action.aspeed))
                break
 
    def do_animation(self):
        for action in self.animations:
            self.do_action(action.name)
            time.sleep(action.exe_time)
            
