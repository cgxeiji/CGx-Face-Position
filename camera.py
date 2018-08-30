from __future__ import print_function

import ConfigParser
import datetime
import logging
import os.path
import sys
import threading
import time
import traceback
import types
from sys import stdout
import random

import numpy as np

import cv2
from libs.bridge import Bridge
from libs.net import NetManager
from libs.robot_net import Robot
from libs.saver import PictureSaver
from libs.utils import get_config_variable as gcv
from libs.visual import Visual


def main():
    camera = cv2.VideoCapture(gcv('camera id', 'int'))
    camera.set(3, 1920)  # 1280
    camera.set(4, 1080)  # 1024

    picture_save_enabled = False
    picture_save = None
    current_save_folder = "Setup"

    space_override = gcv('space override', 'bool')

    visual = Visual(camera)
    visual.start()

    network = NetManager(gcv('unity ip', 'string'), gcv('unity port', 'int'))
    network.on_data_received = types.MethodType(on_data_received, network)
    network.start()

    robot = Robot()
    tracking = False

    bridge = Bridge(robot)
    bridge.shuffle()

    cross_point = (0, 0, 0)

    before_time = time.time()
    face_time = time.time()
    face_lost = False

    face_lost_timeout = gcv('face lost timeout', 'float')

    monitor_is_moving = False
    is_experiment = False
    min_time = gcv('min monitor time', 'int')
    max_time = gcv('max monitor time', 'int')

    move_timer = time.time()
    move_timeout = 1  # second
    user_input_timer = time.time()
    extra_timeout = gcv('monitor timeout', 'int')
    user_input_timeout = extra_timeout

    try:
        while True:
            ret, img = camera.read()
            save_img = img

            if visual.img is not None:
                try:
                    hud = visual.img
                    ret, mask = cv2.threshold(cv2.cvtColor(
                        hud, cv2.COLOR_BGR2GRAY), 10, 255, cv2.THRESH_BINARY)
                    if mask is not None:
                        img = cv2.bitwise_and(
                            img, img, mask=cv2.bitwise_not(mask))
                    img = cv2.add(img, hud)
                finally:
                    pass

            color = (0, 0, 255)
            if picture_save_enabled:
                color = (0, 255, 0)
            location = 'transition zone'
            (ex, ey, ed) = visual.get_center_pixel()

            _pos = visual.get_center()
            _angle = visual.get_angle()

            cols, rows, dim = img.shape
            img = cv2.line(
                img, (cross_point[0], 0), (cross_point[0], cols), color)
            img = cv2.line(
                img, (0, cross_point[1]), (rows, cross_point[1]), color)
            cv2.putText(img, "Monitor moving: {}, for {}s".format(
                monitor_is_moving,
                np.clip(user_input_timeout -
                        (time.time() - user_input_timer),
                        0, None) if monitor_is_moving else 0),
                        (10, 65), visual.font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow("img", img)

            pose_name = ""
            pose_time = 0

            (ex, ey, ed) = visual.get_center()

            if time.time() - before_time > 0.1:
                (x, y, z) = visual.get_center()
                logging.info("face_data->{:.3f}, {:.3f}, {:.3f}, {:.3f}, {}, {:.3f}".format(
                    x, y, z, visual.get_angle(), pose_name, pose_time))
                network.send_to("Head", "{:.3f},{:.3f},{:.3f},{:.3f}".format(
                    x, y, z, visual.get_angle()))

                before_time = time.time()

            if is_experiment and not monitor_is_moving:
                if time.time() - move_timer > move_timeout:
                    _action, _timeout = bridge.do_random()
                    user_input_timeout = _timeout + extra_timeout
                    if _action == '':
                        _action = "After"
                    if picture_save_enabled:
                        current_save_folder = _action
                        picture_save.cd(
                            "{}/{}".format(save_img_path, current_save_folder))
                    monitor_is_moving = True
                    move_timer = time.time()
                    user_input_timer = time.time()
            elif is_experiment and monitor_is_moving:
                if time.time() - user_input_timer > user_input_timeout:
                    logging.info("user->{}".format("timeout"))
                    bridge.do_action("Default Fast")
                    monitor_is_moving = False
                    move_timeout = random.randint(min_time, max_time)
                    move_timer = time.time()

            if picture_save_enabled:
                picture_save.update(save_img)

            c = cv2.waitKey(1)
            if c == 27:
                break
            elif c == ord('a'):
                cross_point = visual.get_center_pixel()
                visual.set_center()
                logging.info("Calibration done!")
            elif c == ord('x'):
                print("{}, {} at {}".format(
                    visual.get_center(), visual.get_angle(), location))
            elif c == ord('z'):
                print("Manual override to Default Location")
                logging.info("user->override")
                bridge.do_action("Default Fast")
                monitor_is_moving = False
                move_timeout = random.randint(min_time, max_time)
                move_timer = time.time()
            elif c == ord('t'):
                tracking = not tracking
                print("Tracking: {}".format(tracking))
            elif c == ord('k'):
                print("Typing activity")
                logging.info("Typing activity")
            elif c == ord('r'):
                print("Reading activity")
                logging.info("Reading activity")
            elif c == ord('s'):
                print("Start experiment!")
                logging.info("Start experiment!")
                move_timeout = random.randint(min_time, max_time)
                move_timer = time.time()
                is_experiment = True
            elif c == ord(' '):
                logging.info("user->{}".format("detect"))
                if space_override:
                    bridge.do_action("Default Fast")
                    monitor_is_moving = False
                    move_timeout = random.randint(min_time, max_time)
                    move_timer = time.time()
                if picture_save_enabled:
                    picture_save.set_detected(True)
            elif c == ord('p'):
                if not picture_save_enabled:
                    save_img_path = "img/{:%Y-%m-%d_%H-%M-%S}".format(
                        datetime.datetime.now())

                    try:
                        os.mkdir("img")
                        print("New directory 'img' created!")
                    except OSError:
                        pass

                    try:
                        os.mkdir(save_img_path)
                        print("Directory {} created!".format(save_img_path))
                    except OSError:
                        print("Directory {} already exists!".format(save_img_path))

                    picture_save = PictureSaver(0.5,
                                                "{}/{}".format(save_img_path, current_save_folder))
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


def on_data_received(self, client, data):
    print("From '{}': {}".format(client.name, data))
    if '$name' in data:
        text = data.split(':')
        client.name = text[1].strip()
        print("Client '{}' [{}] changed names!".format(
            client.name, client.address))


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s->%(asctime)s->%(message)s',
                        filename='logs/{:%Y-%m-%d_%H-%M}.log'.format(datetime.datetime.now()), level=logging.INFO)
    main()
