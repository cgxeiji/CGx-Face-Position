from __future__ import print_function
from sys import stdout
import os.path
import sys
import traceback
import logging
import cv2
import numpy as np
import time

def main():
    abs_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(abs_path, 'lbp/frontal.xml')
    faceCascade = cv2.CascadeClassifier(path)
    if faceCascade.empty():
        raise Exception("Face Classifier not found!", path)

    camera = cv2.VideoCapture(1)

    while True:
        ret_val, img = camera.read()

        faces = []
        faces = faceCascade.detectMultiScale(img, 1.1, 2, 0|cv2.CASCADE_SCALE_IMAGE, (0,0), (0,0))

        if len(faces) != 0:
            (x, y, w, h) = get_biggest(faces)
            img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255))

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