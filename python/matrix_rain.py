import random
import math

import LEDMatrix
import board
import time
import config

from LEDMatrix import LEDMatrix, Pi5Pixelbuf
from typing import Tuple

NEOPIXEL = board.D13
current_brightness = 0.04
pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=current_brightness)

class MatrixRain:
    """
    Simple Matrix-style vertical green rain.
    Usage:
      rain = MatrixRain(width=32, height=32, density=0.02, tail=8)
      while True:
          rain.update(pixels)   # pixels may be a flat Pi5Pixelbuf (len 1024) or a 32x32 int array
          pixels.show()         # if using LED buffer
          time.sleep(0.05)
    """
    def __init__(self, width: int = 32, height: int = 32, density: float = 0.02, tail: int = 8, fade_factor: float = 0.75):
        self.width = width
        self.height = height
        self.density = density
        self.tail = tail
        self.fade_factor = fade_factor
        # columns hold head y (int) or -1 if inactive
        self.columns = [-1] * width

    def _is_flat_buf(self, pixels) -> bool:
        # flat buffer like Pi5Pixelbuf: len == width*height and elements are tuples
        try:
            return len(pixels) == self.width * self.height and not isinstance(pixels[0], int)
        except Exception:
            return False

    def _is_2d_int(self, pixels) -> bool:
        try:
            return len(pixels) == self.height and len(pixels[0]) == self.width and isinstance(pixels[0][0], int)
        except Exception:
            return False

    def update(self, pixels):
        flat = self._is_flat_buf(pixels)
        int2d = self._is_2d_int(pixels)

        # fade whole screen a bit to keep trails
        if flat:
            for i in range(self.width * self.height):
                col = pixels[i]
                # expect tuple (r,g,b)
                r, g, b = col if isinstance(col, tuple) and len(col) == 3 else (0, 0, 0)
                g = int(g * self.fade_factor)
                r = int(r * self.fade_factor)
                b = int(b * self.fade_factor)
                pixels[i] = (r, g, b)
        elif int2d:
            for y in range(self.height):
                row = pixels[y]
                for x in range(self.width):
                    row[x] = int(row[x] * self.fade_factor)

        def set_pixel(x, y, g_value):
            if not (0 <= x < self.width and 0 <= y < self.height):
                return
            if flat:
                idx = y * self.width + x
                # set green with small blue to make it "Matrix"-like if desired
                pixels[idx] = (0, int(g_value), 0)
            elif int2d:
                pixels[y][x] = int(g_value)

        # possibly start new drops
        for x in range(self.width):
            if self.columns[x] == -1:
                if random.random() < self.density:
                    self.columns[x] = 0  # start at top
            else:
                y = self.columns[x]
                # head pixel (bright)
                set_pixel(x, y, 255)
                # tail
                for t in range(1, self.tail):
                    py = y - t
                    if py < 0:
                        break
                    intensity = 255 * (1.0 - (t / float(self.tail)))
                    set_pixel(x, py, max(0, int(intensity)))
                # advance head
                self.columns[x] += 1
                # deactivate when tail passed bottom
                if self.columns[x] - self.tail > self.height:
                    self.columns[x] = -1

def rotate_pixels_180(pixels, width: int = 32, height: int = 32):
    """
    Rotate a flat Pi5Pixelbuf (len width*height with (r,g,b) tuples)
    or a 2D int array (height x width) by 180 degrees in-place.
    """
    # detect flat buffer (tuples) vs 2D int array
    try:
 #       if len(pixels) == width * height and (len(pixels) == 0 or isinstance(pixels[0], tuple)):
            # flat buffer: create temp and copy back
            out = [None] * (width * height)
            for y in range(height):
                for x in range(width):
                    i = y * width + x
                    j = (height - 1 - y) * width + (width - 1 - x)
                    out[j] = pixels[i]
            for k in range(width * height):
                pixels[k] = out[k]
            return
    except Exception:
        pass

try:
    #pixels.fill(0)
    #pixels.show()

    # wait for database to start
    while not config.is_db_available():
        time.sleep(0.3)

    matrix = MatrixRain(width=32, height=32, density=0.02, tail=8)

    config_refresh_time_out = 0
    config = config.Config()
    time_stop_start = time.time()
    config.write_stats( "frequenz", str(0))

    while True:
        angle_offset = 0.0
        while True:                 
            pixels.fill(0)

            # refresh brightness if changed
            if time.time() > config_refresh_time_out:
                brightness = config.get('brightness')

                if brightness is not None:
                    brightness = float( brightness )

                    if current_brightness != brightness:
                        current_brightness = brightness
                        pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=current_brightness)

                else:
                    print( "is none\n" )

                config_refresh_time_out = time.time() + 0.5

            matrix.update(pixels)

            # rotate the buffer 180 degrees before showing
            rotate_pixels_180(pixels, width=matrix.width, height=matrix.height)

            pixels.show()

            time.sleep(0.01)

finally:
    time.sleep(.02)
    #pixels.fill(0)
    #pixels.show()                    