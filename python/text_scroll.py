#!/usr/bin/python
"""Horizontal text marquee for the UselessPope 32x32 LED matrix.

Scrolls the value of the CONFIG key ``scroll_text`` (default "LAN 2.1")
right-to-left in large letters that fill the panel height. The text is re-read
from the database every 0.5 s, so it can be changed live without restarting the
process. Brightness is hot-reloaded from CONFIG ``brightness`` like the other
animations.

Register (once):
    INSERT INTO CONFIG (key, value, hist_an_user, hist_ae_user, hist_lo_user)
    VALUES ('scroll_text', 'LAN 2.1', 'papst', 'papst', 'papst');
"""

import time

import board
import config

from PIL import Image, ImageDraw, ImageFont

from LEDMatrix import LEDMatrix

NEOPIXEL = board.D13
MATRIX_SIZE = 32        # display is 32x32
TEXT_HEIGHT = 30        # rendered text height in pixels (leaves a 1px margin)
MARGIN = MATRIX_SIZE    # blank columns before/after the text
SCROLL_STEP_MS = 0.02   # per-frame delay

CONFIG_KEY = "scroll_text"
DEFAULT_TEXT = "LAN 2.1"

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

current_brightness = 0.04
pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=current_brightness)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_strip(text: str) -> Image.Image:
    """Render text into a 32px-tall 'L' strip padded with MARGIN on each side."""
    font = load_font(48)

    # Measure the text with the big font, then render it tightly cropped.
    measure = Image.new("L", (8, 8), 0)
    draw = ImageDraw.Draw(measure)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_w = max(1, right - left)
    text_h = max(1, bottom - top)

    pad = 2
    text_img = Image.new("L", (text_w + 2 * pad, text_h + 2 * pad), 0)
    draw = ImageDraw.Draw(text_img)
    draw.text((pad - left, pad - top), text, fill=255, font=font)

    # Scale to fill the panel height, preserving aspect ratio.
    new_w = max(1, int(round(text_img.width * TEXT_HEIGHT / text_img.height)))
    text_img = text_img.resize((new_w, TEXT_HEIGHT), Image.Resampling.LANCZOS)

    strip = Image.new("L", (new_w + 2 * MARGIN, MATRIX_SIZE), 0)
    strip.paste(text_img, (MARGIN, (MATRIX_SIZE - TEXT_HEIGHT) // 2))
    return strip


def draw_frame(offset: int, strip_bytes: bytes, strip_width: int) -> None:
    """Blit the 32x32 window at ``offset`` into the LED buffer.

    The panel is mounted upside-down, so every pixel (x, y) is written to the
    rotated position (31-x, 31-y) — i.e. the frame is rotated 180 degrees.
    """
    for y in range(MATRIX_SIZE):
        row = y * strip_width
        dst_row = (MATRIX_SIZE - 1 - y) * MATRIX_SIZE
        for x in range(MATRIX_SIZE):
            sx = offset + x
            v = strip_bytes[row + sx] if 0 <= sx < strip_width else 0
            pixels[dst_row + (MATRIX_SIZE - 1 - x)] = (v, v, v)


def resolve_text(conf: config.Config) -> str:
    text = conf.get(CONFIG_KEY)
    if text is None or text == "":
        text = DEFAULT_TEXT
    return text


try:
    # Wait for MariaDB, then load initial state.
    while not config.is_db_available():
        time.sleep(0.3)

    config_refresh_time_out = 0
    conf = config.Config()

    text = resolve_text(conf)
    strip = build_strip(text)
    strip_bytes = strip.tobytes()
    strip_width = strip.width
    offset = 0

    while True:
        # Refresh brightness and text from the database every 0.5 s.
        if time.time() > config_refresh_time_out:
            brightness = conf.get("brightness")
            if brightness is not None:
                brightness = float(brightness)
                if brightness != current_brightness:
                    current_brightness = brightness
                    pixels = LEDMatrix(
                        NEOPIXEL, auto_write=False, brightness=current_brightness
                    )

            new_text = resolve_text(conf)
            if new_text != text:
                text = new_text
                strip = build_strip(text)
                strip_bytes = strip.tobytes()
                strip_width = strip.width
                offset = 0

            config_refresh_time_out = time.time() + 0.5

        pixels.fill(0)
        draw_frame(offset, strip_bytes, strip_width)
        pixels.show()

        offset += 1
        if offset >= strip_width:
            offset = 0

        time.sleep(SCROLL_STEP_MS)

finally:
    time.sleep(0.02)
    pixels.fill(0)
    pixels.show()
