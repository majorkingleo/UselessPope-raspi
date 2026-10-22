# LED matrix & animations

The display is a 32×32 NeoPixel grid made of four 16×16 panels = 1024 pixels.
Color order is **GRB**. The physical data pin is `board.D13` (SPI-based
NeoPixel on Pi 5), driven through `adafruit_raspberry_pi5_neopixel_write`.

## `LEDMatrix.py`

- `Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf)` — transmits via `neopixel_write`.
- `LEDMatrix(Pi5Pixelbuf)` — presents a flat 32×32 buffer (`pixels[y*32 + x]`)
  and remaps it onto the four physical panels in `_transfer_panel1..4`.
  - `panel_rows = panel_cols = 16`, `panels = 4`, `max_x = max_y = 32`.
  - Constructor: `LEDMatrix(pin, auto_write=..., brightness=..., byteorder="GRB")`.
- `draw_filled_circle(cx, cy, radius, pixels, color)` — helper used by several
  animations; draws with edge fade.

Typical instantiation at module top level:

```python
import board
from LEDMatrix import LEDMatrix
NEOPIXEL = board.D13
pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=0.04)
```

## Standard animation loop pattern

`pope_default_rotating_color_wheel.py`, `pope_red_eyes.py`, `matrix_rain.py`,
and `screen_off.py` all follow the same skeleton:

```python
# wait for database to start
while not config.is_db_available():
    time.sleep(0.3)

config_refresh_time_out = 0
config = config.Config()

while True:
    # ... draw into pixels ...
    # refresh brightness if changed (every 0.5 s)
    if time.time() > config_refresh_time_out:
        brightness = config.get('brightness')
        if brightness is not None:
            brightness = float(brightness)
            if current_brightness != brightness:
                current_brightness = brightness
                pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=current_brightness)
        config_refresh_time_out = time.time() + 0.5
    pixels.show()
    time.sleep(0.01)
```

Key points:

- `brightness` is read as a **string** and cast to `float`.
- Reassigning `pixels` re-creates the whole buffer (this is how hot-reload of
  brightness works — there is no in-place brightness setter used in these
  scripts).
- Rotation counters are written once per full visual cycle:
  `config.write_stats("frequenz", str(int(time_elapsed*60)))` and
  `config.write_stats("umdrehungen", str(rotations))`.

## Animation inventory

| file | what it shows | DB interaction |
|------|---------------|----------------|
| `pope_default_rotating_color_wheel.py` | spinning HSV color wheel + white "eyes" | `brightness`, `umdrehungen`, `frequenz` |
| `pope_red_eyes.py` | same wheel with red eye dots | same as above |
| `matrix_rain.py` | green Matrix rain, rotated 180° | `brightness`, `frequenz` |
| `snake_duel.py` | two-AI snake duel | `brightness`, `snake_p1_wins`, `snake_p2_wins` |
| `screen_off.py` | blank / off screen | `frequenz` (writes 0) |
| `text_scroll.py` | horizontal marquee of `CONFIG.scroll_text` (default `LAN 2.1`) in huge letters | `brightness`, `scroll_text` |
| `led_animation.py` | adafruit_led_animation rainbow sequence | none |
| `send_image.py` | static image or animated GIF (CLI arg) | none |
| `light_chain_led_*.py`, `led_spi.py` | single-chain / SPI experiments | none |

## `text_scroll.py` (text marquee)

Scrolls the value of `CONFIG` key `scroll_text` right-to-left in letters that
fill the 32px panel height (rendered with Pillow + DejaVuSans-Bold, scaled to
30px tall). Text and brightness are both re-read every 0.5 s, so the message can
be changed live without restarting the process. Falls back to `LAN 2.1` when the
key is missing or empty.

## `send_image.py` (not a daemon)

Usage: `python3 send_image.py <image-file>` — resizes to 32×32, supports GIF by
looping frames with per-frame durations. Brightness fixed at 0.2, no DB access.

## How the active animation is selected

1. The broker owns `current_animation` (an integer index).
2. `ring_animation.py` (GPIO-triggered) does the cycling in Python:
   - reads `current_animation`, increments it (wrapping to `0` when
     `animation<N>` is missing),
   - writes the new index back via `config.put('current_animation', ...)`,
   - inserts the resolved `animation<N>` file path into `PLAY_QUEUE_ANIMATION`.
3. The broker dequeues `PLAY_QUEUE_ANIMATION`, stops the running animation
   process, and launches the new one.

## Adding a new animation (checklist)

1. Copy the loop skeleton above (wait-for-DB + brightness poll + `pixels.show()`).
2. Draw into `pixels` as a flat 32×32 buffer (`pixels[y*32 + x] = (r, g, b)`).
3. Put the file in `python/` and register it:
   - add `insert_config("animation<N>", "/home/papst/UselessPope-raspi/python/<name>.py")`
     and `insert_config("animation<N>_title", "...")` in
     `~/UselessPope-Broker/src/main.cc`, **or**
   - insert the `CONFIG` rows manually (see database.md).
4. Optionally write stats via `config.write_stats(...)`.
5. Test standalone: `python3 python/<name>.py` (needs MariaDB up and the
   hardware, or at least the GPIO/board import to succeed).
