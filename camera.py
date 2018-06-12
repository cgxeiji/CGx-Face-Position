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

def main():
    camera = cv2.VideoCapture(1)

    abs_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(abs_path, 'lbp/frontal.xml')
    faceCascade = cv2.CascadeClassifier(path)

    path = os.path.join(abs_path, 'lbp/right.xml')
    rightCascade = cv2.CascadeClassifier(path)

    path = os.path.join(abs_path, 'lbp/left.xml')
    leftCascade = cv2.CascadeClassifier(path)

    face_roi = ROI(1000,1000)

    if faceCascade.empty():
        raise Exception("Face Classifier not found!", path)

    

    while True:
        ret_val, img = camera.read()

        roi = face_roi.get_roi(img)
        min_size, max_size = face_roi.get_size()

        faces = []
        faces = faceCascade.detectMultiScale(roi, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, min_size, max_size)

        if len(faces) == 0:
            if face_roi.is_enabled():
                face_roi.enable(False)
        elif len(faces) != 0:
            (x, y, w, h) = get_biggest(faces)
            face_roi.set_roi(x, y, w, h)
            pt1, pt2 = face_roi.get_rect()
            img = cv2.rectangle(img, pt1, pt2, (0, 0, 255))
        
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
        
        cv2.imshow("test", img)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()

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