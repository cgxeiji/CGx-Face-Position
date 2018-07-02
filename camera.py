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

from libs.net import NetManager
from libs.robot_net import Robot
from libs.bridge import Bridge
from libs.saver import PictureSaver
from libs.visual import Visual

def main():
    camera = cv2.VideoCapture(0)
    camera.set(3, 1280)
    camera.set(4, 1024)

    picture_save_enabled = False
    
    visual = Visual(camera)
    visual.start()

    network = NetManager()
    network.start()

    robot = Robot()
    tracking = False

    bridge = Bridge(robot)

    cross_point = (0, 0, 0)

    before_time = time.time()
    face_time = time.time()
    face_lost = False

    try:
        while True:
            ret, img = camera.read()
            #if visual.roi is not None:
            #    cv2.imshow("roi", visual.roi)
                
            if visual.img is not None:
                try:
                    hud = visual.img
                    ret, mask = cv2.threshold(cv2.cvtColor(hud,cv2.COLOR_BGR2GRAY), 10, 255, cv2.THRESH_BINARY)
                    if mask is not None:
                        img = cv2.bitwise_and(img, img, mask=cv2.bitwise_not(mask))
                    img = cv2.add(img, hud)
                finally:
                    pass


            color = (0, 0, 255)
            if picture_save_enabled:
                color = (0, 255, 0)
            location = 'transition zone'
            (ex, ey, ed) = visual.get_center_pixel()
            #distance = max([abs(cross_point[0] - ex), abs(cross_point[1]- ey), abs(cross_point[2] - ed)*10])

            _pos = visual.get_center()
            _angle = visual.get_angle()

            pose_name = "CGx Bug"
            pose_time = 0.0

            if visual.face_detected:
                face_time = time.time()
                face_lost = False
                pose_name, pose_time = bridge.eval(_pos, _angle)
            elif time.time() - face_time > 10.0 and not face_lost:
                bridge.restart_zone_timers()
                threading.Timer(0.1, bridge.do_animation).start()
                face_lost = True
            else:
                pose_name = "Face Lost"
                pose_time = time.time() - face_time

            location = "{} {:5.2f}s".format(pose_name, pose_time)

            cols, rows, dim = img.shape
            img = cv2.line(img, (cross_point[0], 0), (cross_point[0], cols), color)
            img = cv2.line(img, (0, cross_point[1]), (rows, cross_point[1]), color)
            cv2.putText(img, "Zone: {}".format(location), (10, 65), visual.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            cv2.imshow("img", img)

            (ex, ey, ed) = visual.get_center()
            
            if time.time() - before_time > 0.1:
                (x, y, z) = visual.get_center()
                logging.info("face_data->{:.3f}, {:.3f}, {:.3f}, {:.3f}, {}, {:.3f}".format(x, y, z, visual.get_angle(), pose_name, pose_time))

                before_time = time.time()
            
            if picture_save_enabled:
                picture_save.update(img)

            c = cv2.waitKey(1)
            if c == 27:
                break
            elif c == ord('a'):
                cross_point = visual.get_center_pixel()
                visual.set_center()
                logging.info("Calibration done!")
            elif c == ord('x'):
                print("{}, {} at {}".format(visual.get_center(), visual.get_angle(), location))
            elif c == ord('z'):
                robot.move((0, 0, 0), (0, 0, 0))
            elif c == ord('t'):
                tracking = not tracking
                print("Tracking: {}".format(tracking))
            elif c == ord('p'):
                if not picture_save_enabled:
                    picture_folder_path = 'frames/{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())
                    if not os.path.exists(picture_folder_path):
                        os.makedirs(picture_folder_path)

                    picture_save = PictureSaver(5, picture_folder_path)
                    picture_save.start()
                    logging.info("Start recording!")
                else:
                    picture_save.stop()
                    picture_save.join()
                    logging.info("Stop recording!")

                picture_save_enabled = not picture_save_enabled

    except:
        logging.exception("There was an error!")

    finally:
        cv2.destroyAllWindows()
        if picture_save_enabled:
            picture_save.stop()
            picture_save.join()
        visual.stop()
        visual.join()
        network.stop()
        robot.stop()

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s->%(asctime)s->%(message)s', filename='logs/{:%Y-%m-%d_%H-%M}.log'.format(datetime.datetime.now()), level=logging.INFO)
    main()
