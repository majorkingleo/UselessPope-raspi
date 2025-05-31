import time

import adafruit_pixelbuf
import board
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.sequence import AnimationSequence
from adafruit_raspberry_pi5_neopixel_write import neopixel_write
from typing import Tuple
import LEDMatrix
from LEDMatrix import LEDMatrix, Pi5Pixelbuf


NEOPIXEL = board.D13
num_pixels = 16*16*4


#pixels = Pi5Pixelbuf(NEOPIXEL, num_pixels, auto_write=True, byteorder="GRB", brightness=0.2)
pixels = LEDMatrix(NEOPIXEL, auto_write=True, brightness=0.2)

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

def draw_x(pixels:Pi5Pixelbuf):
    for x in range(0,16*2):
        for y in range(0,16*2):
            pixels[x*y] = (255,0,0)

    for x in range(16*2-1,0,-1):
        for y in range(16*2-1,0,-1):
            pixels[x*y] = (255,0,0)


def draw_l(offset:int, pixels:Pi5Pixelbuf):
    for y in range(0,16*2):
        pixels[offset*(y)] = (255,(y*10)%255,0)

def draw__1(offset:int, pixels:Pi5Pixelbuf):
    for x in range(0,16*2):
        print(x)
        pixels[offset+x] = (255,(x*10)%255,0)

def draw__2(offset:int, pixels:Pi5Pixelbuf):
    for x in range(0,16*2):
        print(x)
        pixels[offset+x] = (0,255,(x*10)%255)

def draw_filled_circle1(cx: int, cy: int, radius: int, pixels: Pi5Pixelbuf, color=(255, 255, 255)):
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if x*x + y*y <= radius*radius:
                px = cx + x
                py = cy + y
                if 0 <= px < 32 and 0 <= py < 32:
                    pixels[py * 32 + px] = color

def draw_filled_circle(cx: int, cy: int, radius: int, pixels: Pi5Pixelbuf, color=(255, 255, 255)):
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            dist_sq = x*x + y*y
            if dist_sq <= radius*radius:
                px = cx + x
                py = cy + y
                if 0 <= px < 32 and 0 <= py < 32:
                    # Fade near the edge: 1.0 at center, 0.2 at edge
                    fade = 1.0 - (dist_sq / (radius*radius))
                    fade = max(0.02, fade)  # Don't go below 0.2
                    faded_color = tuple(int(c * fade) for c in color)
                    pixels[py * 32 + px] = faded_color

try:
    pixels.fill(0)
    pixels.show()

    while True:
        #for i in range( 15, 16 ):
        #    pixels[i] = (255,0,0)
        #pixels[0] = (255,0,0)
        #pixels[1] = (0,255,0)
        #draw_l(0,pixels)
        #draw__1(0,pixels)
        #draw__2(16*2,pixels)
        #draw_filled_circle(16, 16, 14, pixels, color=(0, 255, 0))
        #pixels.show()        
        #break
        animations.animate()
finally:
    time.sleep(.02)
    pixels.fill(0)
    pixels.show()
