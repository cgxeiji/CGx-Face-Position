from __future__ import print_function
from sys import stdout
import os.path
import sys
import traceback
import logging
import cv2
import numpy as np
import time
import datetime
import threading
import ConfigParser
from roi import ROI
from eye import Eye
from smoother import Smoother
from net import NetManager
from pose_sphere import PoseSphere
from robot_net import Robot
from bridge import Bridge
from saver import PictureSaver

class Visual(threading.Thread):
    def __init__(self, camera):
        threading.Thread.__init__(self)
        self.running = False

        abs_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(abs_path, 'lbp/frontal.xml')
        self.faceCascade = cv2.CascadeClassifier(path)

        path = os.path.join(abs_path, 'lbp/eye.xml')
        self.eyeCascade = cv2.CascadeClassifier(path)

        self.face_roi = ROI(1280, 1024)

        self.baseZ = 1
        self.baseX = 1
        self.baseY = 1
        self.alpha = 0.07
        self.beta = -0.08

        self.face_detected = False
        self.eyes_detected = False

        self.eye_right = Eye()
        self.eye_left = Eye()

        self.face_distance = Smoother(20)
        self.face_angle = Smoother(20)

        if self.faceCascade.empty():
            raise Exception("Face Classifier not found!", path)

        self.MAX_TRYOUTS = 10
        self.tryout = self.MAX_TRYOUTS

        self.test_angles = [0, -20, 20, -40, 40]

        self.current_angle = 0

        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.img = None
        self.roi = None
        self.camera = camera

    def run(self):
        self.running = True
        while self.running:
            ret_val, img = self.camera.read()

            if img is None:
                continue

            hud = np.zeros(img.shape, np.uint8)

            roi = self.face_roi.get_roi(img)
            min_size, max_size = self.face_roi.get_size()

            faces = []
            _roi = roi

            if self.face_roi.is_enabled():
                for angle in self.test_angles:
                    if angle != 0:
                        cols, rows, _c = roi.shape
                        M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
                        _roi = cv2.warpAffine(roi,M,(cols,rows))
                    faces = self.faceCascade.detectMultiScale(_roi, 1.05, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)
                    if len(faces) != 0:
                        self.current_angle = angle
                        roi = _roi
                        break
            else:
                __roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                for angle in self.test_angles:
                    if angle != 0:
                        cols, rows = __roi.shape
                        M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
                        _roi = cv2.warpAffine(__roi,M,(cols,rows))
                    faces = self.faceCascade.detectMultiScale(_roi, 1.4, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)
                    if len(faces) != 0:
                        current_angle = angle
                        #roi = _roi
                        break

            eyes_loc = []

            if len(faces) == 0:
                if self.face_roi.is_enabled():
                    self.tryout -= 1
                    if self.tryout <= 0:
                        self.face_roi.enable(False)
            elif len(faces) != 0:
                if not self.face_roi.is_enabled():
                    self.tryout = self.MAX_TRYOUTS
                (x, y, w, h) = get_biggest(faces)
                self.face_roi.set_roi(x, y, w, h)
                pt1, pt2 = self.face_roi.get_rect()
                hud = cv2.rectangle(hud, pt1, pt2, (0, 0, 255))
            
                #if self.face_roi.is_enabled():
                eyes = []
                cols, rows, _c = roi.shape
                min_size = tuple(int(x / 5) for x in (cols, rows))
                max_size = tuple(int(x / 4) for x in (cols, rows))
                eyes = self.eyeCascade.detectMultiScale(roi, 1.05, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)

                if len(eyes) != 0:
                    #self.tryout = self.MAX_TRYOUTS
                    for (x, y, w, h) in eyes:
                        if y > rows/3:
                            continue
                        
                        roi = cv2.rectangle(roi, (x, y), (x+w, y+h), (255, 0, 0))
                        text = "({}, {})".format(x, y)
                        cv2.putText(roi, text, (x, y), self.font, 0.5,(255,255,255),1,cv2.LINE_AA)
                        
                        (x1, y1) = rotate((x+w/2, y+h/2), (cols/2, rows/2), self.current_angle)

                        x1 /= self.face_roi._scale_factor
                        y1 /= self.face_roi._scale_factor
                        w /= self.face_roi._scale_factor
                        w /= 5

                        pt1, pt2 = self.face_roi.get_rect()
                        ps = (int(x1) + pt1[0], int(y1) + pt1[1])

                        eyes_loc.append(ps)

                        #text = "({}, {})".format(ps[0], ps[1])
                        #cv2.putText(img, text, ps, font, 0.5,(255,255,255),2,cv2.LINE_AA)

            eyes_loc = sorted(eyes_loc, key=lambda x: x[0])
            self.eyes_detected = False
            if len(eyes_loc) > 1:
                self.eye_right.input(eyes_loc[0])
                self.eye_left.input(eyes_loc[1])
                self.eyes_detected = True

            hud = cv2.line(hud, self.eye_right.position(), self.eye_left.position(), (0, 255, 0))
            (rx, ry) = self.eye_right.position()
            (lx, ly) = self.eye_left.position()

            hud = cv2.circle(hud, self.eye_right.position(), 5, (255, 255, 255))
            hud = cv2.circle(hud, self.eye_left.position(), 5, (255, 255, 255))

            self.face_angle.input(np.arctan2(ly - ry, lx - rx) * 180.0 / np.pi)
            _d = np.sqrt(np.power(ly - ry, 2) + np.power(lx - rx, 2))
            self.face_distance.input(0.0043 * np.power(_d, 2) - 1.2678 * _d + 116.02)

            #pt1, pt2 = self.face_roi.get_rect()
            pt1 = (10, 45)
            hud = cv2.rectangle(hud, (pt1[0] - 10, pt1[1] + 25), (pt1[0] + 800, pt1[1] - 45), (30, 30, 30), -1)
            text = "angle: {0:.2f} degrees                [{1:%Y-%m-%d %H:%M:%S}]".format(self.face_angle.value(), datetime.datetime.now())
            cv2.putText(hud, text, (pt1[0], pt1[1] - 25), self.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            text = "distance: {0:.2f} cm [{1:.2f} pixels]".format(self.face_distance.value(), _d)
            cv2.putText(hud, text, (pt1[0], pt1[1] - 10), self.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            (_x, _y, _z) = self.get_center_pixel()
            (__x, __y, __z) = self.get_center()
            text = "Face({}) Eyes({}): {:.2f} [{:.2f}] x {:.2f} [{:.2f}] y {:.2f} [{:.2f}] z".format(self.face_roi.is_enabled(), self.eyes_detected, __x, _x, __y, _y, __z, _z)
            cv2.putText(hud, text, (pt1[0], pt1[1] + 5), self.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)

            self.img = hud
            self.roi = roi

    def stop(self):
        self.running = False
    
    def get_center_pixel(self):
        return ((self.eye_left.position()[0] + self.eye_right.position()[0]) / 2, (self.eye_left.position()[1] + self.eye_right.position()[1]) / 2, self.face_distance.value())

    def get_center(self):
        (x, y, z) = self.get_center_pixel();
        return (self.get_transform(x - self.baseX, self.alpha), self.get_transform(y - self.baseY, self.beta), z - self.baseZ)

    def set_center(self):
        (self.baseX, self.baseY, self.baseZ) = self.get_center_pixel()

    def get_angle(self):
        return self.face_angle.value()

    def get_transform(self, pixel, value):
        return self.face_distance.value() * pixel * value / self.baseZ


def main():
    camera = cv2.VideoCapture(1)
    camera.set(3, 1280)
    camera.set(4, 1024)

    picture_save_enabled = False

    #default_pose = PoseSphere('safe zone')
    #test_pose = PoseSphere('test zone')
    poses = []
    #poses.append(default_pose)
    #poses.append(test_pose)
    #test_pose.set_sphere((15, 0, 0), 0, 5, 20)
    config = ConfigParser.ConfigParser()
    print(config)
    config.read('poses.ini')
    for section in config.sections():
        print(section)
        priority = config.getint(section, 'priority')

        pose = PoseSphere(section, priority)

        pos = (config.getfloat(section, 'x'), config.getfloat(section, 'y'), config.getfloat(section, 'z'))
        a = config.getfloat(section, 'angle')
        tol = config.getfloat(section, 'tolerance')
        _type = config.get(section, 'type')

        if _type == 'Sphere':
            dia = config.getfloat(section, 'diameter')
            pose.set_sphere(pos, a, dia, tol)
        elif _type == 'Block':
            p2 = (config.getfloat(section, 'x2'), config.getfloat(section, 'y2'), config.getfloat(section, 'z2'))
            pose.set_block(pos, p2, a, dia, tol)

        timer = config.getfloat(section, 'time')
        action = config.get(section, 'action')
        pose.set_action(action, timer)

        poses.append(pose)

    poses.sort(key=lambda x: x.priority, reverse = True)
    
    for pose in poses:
        print("{}: {}".format(pose.priority, pose.name))
    
    visual = Visual(camera)
    visual.start()

    network = NetManager()
    network.start()

    robot = Robot()
    tracking = False

    bridge = Bridge(robot)

    cross_point = (0, 0, 0)

    before_time = time.time()

    try:
        while True:
            ret, img = camera.read()
            #if visual.roi is not None:
            #    cv2.imshow("roi", visual.roi)
                
            if visual.img is not None:
                hud = visual.img
                ret, mask = cv2.threshold(cv2.cvtColor(hud,cv2.COLOR_BGR2GRAY), 10, 255, cv2.THRESH_BINARY)
                img = cv2.bitwise_and(img, img, mask=cv2.bitwise_not(mask))
                img = cv2.add(img, hud)

            color = (0, 0, 255)
            location = 'transition zone'
            (ex, ey, ed) = visual.get_center_pixel()
            #distance = max([abs(cross_point[0] - ex), abs(cross_point[1]- ey), abs(cross_point[2] - ed)*10])

            _pos = visual.get_center()
            _angle = visual.get_angle()
            in_pose = False
            for pose in poses:
                if in_pose:
                    pose.skip()
                elif pose.check(_pos, _angle):
                    location = "{} {:.2f}s".format(pose.name, pose.get_time())
                    if pose.timeout():
                        bridge.do_action(pose.action)
                    in_pose = True

            cols, rows, dim = img.shape
            img = cv2.line(img, (cross_point[0], 0), (cross_point[0], cols), color)
            img = cv2.line(img, (0, cross_point[1]), (rows, cross_point[1]), color)
            cv2.putText(img, "Zone: {}".format(location), (10, 65), visual.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            cv2.imshow("img", img)

            (ex, ey, ed) = visual.get_center()
            
            network.set_position(ex*10, ey*10, ed*10, visual.get_angle())
            
            
            if time.time() - before_time > 0.5:
                logging.info(network.get_data())

                before_time = time.time()
            
            if picture_save_enabled:
                picture_save.update(img)

            c = cv2.waitKey(1)
            if c == 27:
                break
            elif c == ord('a'):
                cross_point = visual.get_center_pixel()
                visual.set_center()
            elif c == ord('x'):
                print("{}, {} at {}".format(visual.get_center(), visual.get_angle(), location))
            elif c == ord('z'):
                robot.move((0, 0, 0), (0, 0, 0))
            elif c == ord('t'):
                tracking = not tracking
                print("Tracking: {}".format(tracking))
            elif c == ord('p'):
                picture_folder_path = '{:%Y%m%d_%H%M}'.format(datetime.datetime.now())
                if not os.path.exists(picture_folder_path):
                    os.makedirs(picture_folder_path)

                picture_save = PictureSaver(1, picture_folder_path)
                picture_save.start()
                picture_save_enabled = True


    finally:
        cv2.destroyAllWindows()
        if picture_save_enabled:
            picture_save.stop()
            picture_save.join()
        visual.stop()
        visual.join()
        network.stop()
        robot.stop()

def rotate((x, y), (h, k), angle):
    x -= h
    y -= k
    _x = x * np.cos(np.deg2rad(angle)) - y * np.sin(np.deg2rad(angle))
    _y = x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    _x += h
    _y += k

    return (_x, _y)

def get_biggest(faces):
    x = 0
    y = 0
    w = 0
    for (_x, _y, _w, _h) in faces:
        if _w > w:
            x = _x
            y = _y
            w = _w
    return (x, y, w, w)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: [%(asctime)s] %(message)s', filename='{:%Y-%m-%d_%H-%M}.log'.format(datetime.datetime.now()), level=logging.INFO)
    main()