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


def is_animated_image(filepath: str) -> bool:
    with Image.open(filepath) as img:
        return getattr(img, "is_animated", False)

def show_animated_image(pixels: Pi5Pixelbuf, filepath: str, delay: float = 0.1):
    """
    Loads an animated image (e.g., GIF), resizes each frame to 32x32, and displays the frames in sequence.
    """
    with Image.open(filepath) as img:
        n_frames = getattr(img, "n_frames", 1)
        while True:
            for frame in range(n_frames):
                img.seek(frame)
                frame_img = img.convert("RGB").resize((32, 32), Image.Resampling.LANCZOS)
                frame_array = []
                for y in range(32):
                    row = []
                    for x in range(32):
                        row.append(frame_img.getpixel((x, y)))
                    frame_array.append(row)
                show_image(pixels, frame_array)
                # Get delay from GIF metadata (duration is in milliseconds)
                frame_delay = img.info.get("duration", int(delay * 1000)) / 1000.0
                time.sleep(frame_delay)
            

def show_image(pixels: Pi5Pixelbuf, image_array: list):
    """
    Displays a 32x32 image on the LED matrix.
    """
    for y in range(32):
        for x in range(32):
            pixels[y * 32 + x] = image_array[y][x]
    pixels.show()

if __name__ == "__main__":
    pixels.fill(0)

    if is_animated_image(sys.argv[1]):
        show_animated_image(pixels, sys.argv[1])    
    else:
        show_image(pixels, load_image_to_32x32_array(sys.argv[1]))

