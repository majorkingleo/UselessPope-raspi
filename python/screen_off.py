import math

import LEDMatrix
import board
import time
import config

from LEDMatrix import LEDMatrix, Pi5Pixelbuf, draw_filled_circle
from typing import Tuple

NEOPIXEL = board.D13
current_brightness = 0.04
pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=current_brightness)

try:
    pixels.fill(0)
    pixels.show()

    # wait for database to start
    while not config.is_db_available():
        time.sleep(0.3)

    config_refresh_time_out = 0
    config = config.Config()
    config.write_stats( "frequenz", str(int(0)))

    while True:
        time.sleep(1)

finally:
    time.sleep(.02)
    pixels.fill(0)
    pixels.show()
