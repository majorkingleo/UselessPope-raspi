from PIL import Image
import LEDMatrix
import board
import time
import sys

from LEDMatrix import LEDMatrix, Pi5Pixelbuf
from typing import Tuple

NEOPIXEL = board.D13
pixels = LEDMatrix(NEOPIXEL, auto_write=False, brightness=0.2)

def load_image_to_32x32_array(filepath: str):
    """
    Loads an image file, resizes it to 32x32, and returns a 32x32 array of (R, G, B) tuples.
    Supports BMP, JPEG, PNG, GIF, etc.
    """
    img = Image.open(filepath).convert("RGB")
    img = img.resize((32, 32), Image.Resampling.LANCZOS)
    pixel_array = []
    for y in range(32):
        row = []
        for x in range(32):
            row.append(img.getpixel((x, y)))
        pixel_array.append(row)
    return pixel_array


if __name__ == "__main__":
    pixels.fill(0)

    buf = load_image_to_32x32_array( sys.argv[1] )
    for y in range(32):
        for x in range(32):
            pixels[y * 32 + x] =  buf[y][x]

    pixels.show()

