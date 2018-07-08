import cv2
from utils import Smoother

class ROI(object):
    def __init__(self, max_width, max_height):
        self.is_detected = False
        self._margin = 0.8 # percent
        self._margin_low = 1 - self._margin
        self._margin_high = 1 + self._margin
        self._c_margin = 1 + self._margin / 2
        self._width = 0
        
        self._max_width = max_width
        self._max_height = max_height
        self._mid_max_width = max_width / 2
        self._mid_max_height = max_height / 2

        self.DEFAULT_SCALE_FACTOR = 0.8
        self._scale_factor = self.DEFAULT_SCALE_FACTOR
        

        self._x1 = 0
        self._x2 = 0
        self._y1 = 0
        self._y2 = 0

        self.x1_s = Smoother(2)
        self.x2_s = Smoother(2)
        self.y1_s = Smoother(2)
        self.y2_s = Smoother(2)

        self.w_s = Smoother(2)

    def set_roi(self, x, y, width, height):
        # Take into account the offset of the previous ROI, if available
        # Take into account the scale factor if it is a new face
        if self.is_detected:
            _x = self._x1 + x / self._scale_factor
            _y = self._y1 + y / self._scale_factor
            self._width = width / self._scale_factor
        else:
            _x = x / self._scale_factor
            _y = y / self._scale_factor
            self._width = width / self._scale_factor

        wc = self._c_margin * self._width
        w_by_c_minus_1 = wc - self._width

        # Increase the boundaries by the margin
        self._x1 = int(_x - w_by_c_minus_1)
        if self._x1 < 0:
            self._x1 = 0
        if self._x1 > self._max_width:
            self._x1 = self._max_width
        self._y1 = int(_y - w_by_c_minus_1)
        if self._y1 < 0:
            self._y1 = 0
        if self._y1 > self._max_height:
            self._y1 = self._max_height

        # Assume square shape for speed
        self._x2 = int(_x + wc)
        if self._x2 < 0:
            self._x2 = 0
        if self._x2 > self._max_width:
            self._x2 = self._max_width

        self._y2 = int(_y + wc)
        if self._y2 < 0:
            self._y2 = 0
        if self._y2 > self._max_height:
            self._y2 = self._max_height

        if self.is_detected:
            self.x1_s.input(self._x1)
            self.x2_s.input(self._x2)
            self.y1_s.input(self._y1)
            self.y2_s.input(self._y2)
            self.w_s.input(self._width)
        else:
            self.x1_s.set(self._x1)
            self.x2_s.set(self._x2)
            self.y1_s.set(self._y1)
            self.y2_s.set(self._y2)
            self.w_s.set(self._width)
            # Enable the flag for this ROI
            self.is_detected = True

        self._x1 = self.x1_s.value()
        self._x2 = self.x2_s.value()
        self._y1 = self.y1_s.value()
        self._y2 = self.y2_s.value()
        self._width = self.w_s.value()

    def get_roi(self, image):
        if self.is_detected:
            img = image[self._y1:self._y2, self._x1:self._x2]
            self._scale_factor = 120 / self._width
            cols, rows = img.shape[:2]
            if cols > 0 and rows > 0:
                return cv2.resize(img, (0, 0), fx=self._scale_factor, fy=self._scale_factor)
            else:
                #print("Size error! ({}, {}) in ({},{})({},{})".format(cols, rows, self._y1, self._y2, self._x1, self._x2))
                return image
        else:
            return cv2.resize(image, (0, 0), fx=self._scale_factor, fy=self._scale_factor)

    def get_size(self):
        if self.is_detected:
            # Assuming a square shape for speed
            min_size = int(self._margin_low*self._width)
            max_size = int(self._margin_high*self._width)

            return (min_size, min_size), (max_size, max_size)
        else:
            return (0, 0), (0, 0)

    def enable(self, boolean):
        if boolean == False:
            self._scale_factor = self.DEFAULT_SCALE_FACTOR
        self.is_detected = boolean;

    def is_enabled(self):
        return self.is_detected

    def get_rect(self):
        if self.is_detected:
            return (self._x1, self._y1), (self._x2, self._y2)
        else:
            return (0, 0), (0, 0)

    def center(self):
        x = (self._x1 + self._x2) / 2
        y = (self._y1 + self._y2) / 2

        return x, y
    
    def from_center(self):
        if self.is_detected:
            x = self._mid_max_width - (self._x1 + self._x2) / 2
            y = self._mid_max_height - (self._y1 + self._y2) / 2
            return x, y
        
        return 0, 0

    def set_margin(self, margin):
        self._margin = margin
        self._margin_low = 1 - margin
        self._margin_high = 1 + margin
        self._c_margin = 1 + self._margin / 2

    def set_max(self, max_width, max_height):
        self._max_width = max_width
        self._max_height = max_height
        self._mid_max_width = max_width / 2
        self._mid_max_height = max_height / 2

    def offset(self, x, y):
        self._x1 += x
        self._x2 += x
        self._y1 += y
        self._y2 += y

        if self._x1 < 0:
            self._x1 = 0
        if self._y1 < 0:
            self._y1 = 0

        if self._x2 > self._max_width:
            self._x2 = self._max_width
        if self._y2 > self._max_height:
            self._y2 = self._max_height