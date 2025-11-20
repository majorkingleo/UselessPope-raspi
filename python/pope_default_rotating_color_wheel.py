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

def hsv_to_rgb(h, s, v) -> Tuple[int, int, int]:
    # h in [0, 1], s in [0, 1], v in [0, 1]
    i = int(h * 6)
    f = h * 6 - i
    p = int(255 * v * (1 - s))
    q = int(255 * v * (1 - f * s))
    t = int(255 * v * (1 - (1 - f) * s))
    v = int(255 * v)
    i = i % 6
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    if i == 5:
        return (v, p, q)
    # Default return to satisfy type checker
    return (0, 0, 0)

def draw_color_wheel_circle_classic(cx: int, cy: int, radius: int, pixels: Pi5Pixelbuf, angle_offset: float = 0.0, brightness: float = 1.0):
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            dist_sq = x*x + y*y
            if dist_sq <= radius*radius:
                px = cx + x
                py = cy + y
                if 0 <= px < 32 and 0 <= py < 32:
                    angle = (math.atan2(y, x) + math.pi) / (2 * math.pi)  # 0..1
                    angle = (angle + angle_offset) % 1.0
                    color = hsv_to_rgb(angle, 1.0, brightness)
                    # Optional: fade near the edge
                    fade = 1.0 - (dist_sq / (radius*radius))
                    fade = max(0.1, fade)
                    faded_color = tuple(int(c * fade) for c in color)
                    pixels[py * 32 + px] = faded_color

def draw_color_wheel_circle_spiral(cx: int, cy: int, radius: int, pixels: Pi5Pixelbuf, angle_offset: float = 0.0, brightness: float = 1.0, twist: float = 1.0):
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            dist_sq = x*x + y*y
            if dist_sq <= radius*radius:
                px = cx + x
                py = cy + y
                if 0 <= px < 32 and 0 <= py < 32:
                    angle = (math.atan2(y, x) + math.pi) / (2 * math.pi)  # 0..1
                    # Add twist: the further from center, the more the hue shifts
                    distance = math.sqrt(dist_sq) / radius  # 0..1
                    hue = (angle + angle_offset + twist * distance) % 1.0
                    color = hsv_to_rgb(hue, 1.0, brightness)
                    fade = 1.0 - (dist_sq / (radius*radius))
                    fade = max(0.1, fade)
                    faded_color = tuple(int(c * fade) for c in color)
                    pixels[py * 32 + px] = faded_color



try:
    #pixels.fill(0)
    #pixels.show()

    # wait for database to start
    while not config.is_db_available():
        time.sleep(0.3)

    config_refresh_time_out = 0
    config = config.Config()
    time_stop_start = time.time()
    rotations = config.get_stats("umdrehungen")
    if rotations == None:
        rotations = 0
    else:
        rotations = int(rotations)

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

            draw_color_wheel_circle_spiral(16, 16, 25, pixels, angle_offset=angle_offset, brightness=1.0, twist=5.0)
            draw_filled_circle(14, 15, 5, pixels, color=(255, 255, 255))
            draw_filled_circle(5, 5, 3, pixels, color=(255, 255, 255))
            draw_filled_circle(5, 27, 3, pixels, color=(255, 255, 255))
            draw_filled_circle(27, 5, 3, pixels, color=(255, 255, 255))
            draw_filled_circle(27, 27, 3, pixels, color=(255, 255, 255))
            pixels.show()
            angle_offset -= 0.06
            if angle_offset <= 0.0:
                time_elapsed = time.time() - time_stop_start
                # print( "{0}s".format(time_elapsed))
                time_stop_start = time.time()

                config.write_stats( "frequenz", str(int(time_elapsed*60)))
                rotations += 1
                config.write_stats( "umdrehungen", str(rotations))

                angle_offset = 1
            time.sleep(0.01)

finally:
    time.sleep(.02)
    #pixels.fill(0)
    #pixels.show()
