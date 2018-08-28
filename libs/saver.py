import threading
import datetime
import time

import cv2


class PictureSaver(threading.Thread):
    def __init__(self, timeout, path):
        threading.Thread.__init__(self)
        self.timer = time.time()
        self.timeout = timeout
        self.picture_counter = 0
        self.path = path
        self.img = None
        self.running = False
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.buffer = None

    def run(self):
        self.running = True
        while self.running:
            if time.time() - self.timer > self.timeout:
                if self.buffer is not None:
                    self.img = cv2.rectangle(
                        self.buffer, (0, 1035), (380, 1080), (30, 30, 30), -1)
                    cv2.putText(self.img,
                                "time: {:%H:%M:%S.%f}".format(
                                    datetime.datetime.now()),
                                (10, 1070), self.font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.imwrite("{}/{}.jpg".format(self.path,
                                                   self.picture_counter), self.img)
                    self.picture_counter += 1
                self.timer = time.time()

    def update(self, img):
        self.buffer = img

    def stop(self):
        self.running = False
