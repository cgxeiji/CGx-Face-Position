from __future__ import print_function
from sys import stdout
import os.path
import sys
import traceback
import logging
import cv2
import numpy as np
import time
from roi import ROI
from eye import Eye
from smoother import Smoother

def main():
    camera = cv2.VideoCapture(1)

    abs_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(abs_path, 'lbp/frontal.xml')
    faceCascade = cv2.CascadeClassifier(path)

    path = os.path.join(abs_path, 'lbp/right.xml')
    rightCascade = cv2.CascadeClassifier(path)

    path = os.path.join(abs_path, 'lbp/left.xml')
    leftCascade = cv2.CascadeClassifier(path)

    path = os.path.join(abs_path, 'lbp/eye.xml')
    eyeCascade = cv2.CascadeClassifier(path)

    face_roi = ROI(1000,1000)

    eye_right = Eye()
    eye_left = Eye()

    face_distance = Smoother(20)
    face_angle = Smoother(20)

    if faceCascade.empty():
        raise Exception("Face Classifier not found!", path)

    MAX_TRYOUTS = 10
    tryout = MAX_TRYOUTS

    test_angles = [0, -20, 20, -40, 40]

    current_angle = 0

    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        ret_val, img = camera.read()

        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        roi = face_roi.get_roi(img)
        min_size, max_size = face_roi.get_size()

        faces = []
        _roi = roi

        for angle in test_angles:
            if angle != 0:
                cols, rows, _c = roi.shape
                M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
                _roi = cv2.warpAffine(roi,M,(cols,rows))
            faces = faceCascade.detectMultiScale(_roi, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)
            if len(faces) != 0:
                current_angle = angle
                roi = _roi
                break

        eyes_loc = []

        if len(faces) == 0:
            if face_roi.is_enabled():
                tryout -= 1
                if tryout <= 0:
                    face_roi.enable(False)
        elif len(faces) != 0:
            if not face_roi.is_enabled():
                tryout = MAX_TRYOUTS
            (x, y, w, h) = get_biggest(faces)
            face_roi.set_roi(x, y, w, h)
            pt1, pt2 = face_roi.get_rect()
            img = cv2.rectangle(img, pt1, pt2, (0, 0, 255))
        
            eyes = []
            cols, rows, _c = roi.shape
            min_size = tuple(int(x / 5) for x in (cols, rows))
            max_size = tuple(int(x / 4) for x in (cols, rows))
            eyes = eyeCascade.detectMultiScale(roi, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)

            

            if len(eyes) != 0:
                for (x, y, w, h) in eyes:
                    if y > rows/3:
                        continue
                    
                    roi = cv2.rectangle(roi, (x, y), (x+w, y+h), (255, 0, 0))
                    text = "({}, {})".format(x, y)
                    cv2.putText(roi, text, (x, y), font, 0.5,(255,255,255),1,cv2.LINE_AA)
                    
                    (x1, y1) = rotate((x+w/2, y+h/2), (cols/2, rows/2), current_angle)

                    x1 /= face_roi._scale_factor
                    y1 /= face_roi._scale_factor
                    w /= face_roi._scale_factor
                    w /= 5

                    pt1, pt2 = face_roi.get_rect()
                    ps = (int(x1) + pt1[0], int(y1) + pt1[1])

                    eyes_loc.append(ps)

                    #text = "({}, {})".format(ps[0], ps[1])
                    #cv2.putText(img, text, ps, font, 0.5,(255,255,255),2,cv2.LINE_AA)

        eyes_loc = sorted(eyes_loc, key=lambda x: x[0])
        if len(eyes_loc) > 1:
            eye_right.input(eyes_loc[0])
            eye_left.input(eyes_loc[1])

        img = cv2.line(img, eye_right.position(), eye_left.position(), (0, 255, 0))
        (rx, ry) = eye_right.position()
        (lx, ly) = eye_left.position()

        img = cv2.circle(img, eye_right.position(), 5, (255, 255, 255))
        img = cv2.circle(img, eye_left.position(), 5, (255, 255, 255))

        face_angle.input(np.arctan2(ly - ry, lx - rx) * 180.0 / np.pi)
        _d = np.sqrt(np.power(ly - ry, 2) + np.power(lx - rx, 2))
        face_distance.input(0.0043 * np.power(_d, 2) - 1.2678 * _d + 116.02)

        pt1, pt2 = face_roi.get_rect()
        img = cv2.rectangle(img, (pt1[0] - 10, pt1[1]), (pt1[0] + 300, pt1[1] - 45), (0, 0, 0), -1)
        text = "angle: {0:.2f} degrees".format(face_angle.value())
        cv2.putText(img, text, (pt1[0], pt1[1] - 25), font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)
        text = "distance: {0:.2f} cm [{1:.2f} pixels]".format(face_distance.value(), _d)
        cv2.putText(img, text, (pt1[0], pt1[1] - 10), font, 0.5,(255, 255, 255), 1,cv2.LINE_AA)

        """
        
        eyes = []
        eyes = rightCascade.detectMultiScale(roi, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, (0,0), (0,0))

        if len(eyes) != 0:
            (x, y, w, h) = get_biggest(eyes)
            x /= face_roi._scale_factor
            y /= face_roi._scale_factor
            w /= face_roi._scale_factor
            h /= face_roi._scale_factor
            pt1, pt2 = face_roi.get_rect()
            ps = (int(x) + pt1[0], int(y) + pt1[1])
            pf = (int(x + pt1[0] + w), int(y + pt1[1] + h))
            img = cv2.rectangle(img, ps, pf, (255, 0, 0))
            
        eyes = leftCascade.detectMultiScale(roi, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, (0,0), (0,0))

        if len(eyes) != 0:
            (x, y, w, h) = get_biggest(eyes)
            x /= face_roi._scale_factor
            y /= face_roi._scale_factor
            w /= face_roi._scale_factor
            h /= face_roi._scale_factor
            pt1, pt2 = face_roi.get_rect()
            ps = (int(x) + pt1[0], int(y) + pt1[1])
            pf = (int(x + pt1[0] + w), int(y + pt1[1] + h))
            img = cv2.rectangle(img, ps, pf, (0, 255, 0))

        """
        
        cv2.imshow("roi", roi)
        cv2.imshow("test", img)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()

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