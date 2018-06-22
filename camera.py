from __future__ import print_function
from sys import stdout
import os.path
import sys
import traceback
import logging
import cv2
import numpy as np
import time
import threading
from roi import ROI
from eye import Eye
from smoother import Smoother
from net import NetManager

class Visual(threading.Thread):
    def __init__(self, camera):
        threading.Thread.__init__(self)
        self.running = False

        abs_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(abs_path, 'lbp/frontal.xml')
        self.faceCascade = cv2.CascadeClassifier(path)

        path = os.path.join(abs_path, 'lbp/eye.xml')
        self.eyeCascade = cv2.CascadeClassifier(path)

        self.face_roi = ROI(640, 480)

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
            if len(eyes_loc) > 1:
                self.eye_right.input(eyes_loc[0])
                self.eye_left.input(eyes_loc[1])

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
            hud = cv2.rectangle(hud, (pt1[0] - 10, pt1[1]), (pt1[0] + 300, pt1[1] - 45), (30, 30, 30), -1)
            text = "angle: {0:.2f} degrees".format(self.face_angle.value())
            cv2.putText(hud, text, (pt1[0], pt1[1] - 25), self.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            text = "distance: {0:.2f} cm [{1:.2f} pixels]".format(self.face_distance.value(), _d)
            cv2.putText(hud, text, (pt1[0], pt1[1] - 10), self.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)

            self.img = hud
            self.roi = roi

    def stop(self):
        self.running = False
    
    def get_center(self):
        return ((self.eye_left.position()[0] + self.eye_right.position()[0]) / 2, (self.eye_left.position()[1] + self.eye_right.position()[1]) / 2, self.face_distance.value())

    def get_angle(self):
        return self.face_angle.value()


def main():
    camera = cv2.VideoCapture(1)

    visual = Visual(camera)
    visual.start()

    network = NetManager()
    network.start()

    cross_point = (0, 0, 0)

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

            color = (0, 255, 0)
            (ex, ey, ed) = visual.get_center()
            distance = max([abs(cross_point[0] - ex), abs(cross_point[1]- ey), abs(cross_point[2] - ed)*10])

            if distance > 50:
                color = (0, 0, 255)

            cols, rows, dim = img.shape
            img = cv2.line(img, (cross_point[0], 0), (cross_point[0], cols), color)
            img = cv2.line(img, (0, cross_point[1]), (rows, cross_point[1]), color)
            #cv2.putText(img, str(distance), (10, 50), visual.font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
            cv2.imshow("img", img)
            
            network.set_position(cross_point[0] - ex, cross_point[1] - ey, (cross_point[2] - ed)*10, visual.get_angle())

            c = cv2.waitKey(1)
            if c == 27:
                break
            elif c == ord('a'):
                cross_point = visual.get_center()


    finally:
        cv2.destroyAllWindows()
        visual.stop()
        visual.join()
        network.stop()

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
    main()