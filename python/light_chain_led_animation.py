import time

import board
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.sequence import AnimationSequence
from adafruit_raspberry_pi5_neopixel_write import neopixel_write
from typing import Tuple
import LEDMatrix
from LEDMatrix import Pi5Pixelbuf


NEOPIXEL = board.D12
num_pixels = 50


pixels = Pi5Pixelbuf(NEOPIXEL, num_pixels, auto_write=True, byteorder="GRB", brightness=0.2)

rainbow = Rainbow(pixels, speed=0.02, period=2)
rainbow_chase = RainbowChase(pixels, speed=0.02, size=5, spacing=3)
rainbow_comet = RainbowComet(pixels, speed=0.02, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixels, speed=0.02, num_sparkles=15)




animations = AnimationSequence(
    rainbow,
    rainbow_chase,
    rainbow_comet,
    rainbow_sparkle,
    advance_interval=5,
    auto_clear=True,
)

try:
    pixels.fill(0)
    pixels.show()

    while True:
        animations.animate()

finally:
    time.sleep(.02)
    pixels.fill(0)
    pixels.show()
