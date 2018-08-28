import threading
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

    def run(self):
        self.running = True
        while self.running:
            if time.time() - self.timer > self.timeout:
                if self.img is not None:
                    cv2.imwrite("{}/{}.png".format(self.path,
                                                   self.picture_counter), self.img)
                    self.picture_counter += 1
                self.timer = time.time()

    def update(self, img):
        self.img = img

    def stop(self):
        self.running = False
