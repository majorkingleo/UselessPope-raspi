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


NEOPIXEL = board.D13
num_pixels = 16*16*4

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

class PixelBufLEDMatrix(Pi5Pixelbuf):

    matrix = None
    panel_rows = 16
    panel_cols = 16
    panels = 4
    pixels_per_panel = panel_rows*panel_cols    
    max_pixel_offset = pixels_per_panel * panels - 1 # 1024
    max_x = panel_cols*2
    max_y = panel_rows*2

    def __init__(self, pin, size, **kwargs):        
        super().__init__(pin, size, **kwargs)        

    def _transfer_panel1(self, buf:bytearray, matrix:bytearray):
        # panel 1 (upper left) even rows
        for y in range( 0, self.panel_rows, 2):
            target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + (self.panel_rows*(y+1))
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset-x)*self._bpp+idx_color] = buf[(y*self.max_x+x)*self._bpp+idx_color]


        # panel 1 (upper left) odd rows
        for y in range( 1, self.panel_rows + 1, 2):
            target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + (self.panel_rows*y)+1
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset+x)*self._bpp+idx_color] = buf[(y*self.max_x+x)*self._bpp+idx_color]

    def _transfer_panel2(self, buf:bytearray, matrix:bytearray):
        # panel 2 (upper right) even rows
        for y in range( 0, self.panel_rows, 2):
            target_pixel_row_offset = (self.max_pixel_offset - self.pixels_per_panel) - (self.panel_rows*(y))                
            for x in range( 0, self.panel_rows):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset-x)*self._bpp+idx_color] = buf[(y*self.max_x+x+self.panel_cols)*self._bpp+idx_color]

        # panel 2 (upper right) odd rows        
        for y in range( 1, self.panel_rows + 1, 2):
            target_pixel_row_offset = (self.max_pixel_offset - self.pixels_per_panel) - (self.panel_rows*(y+1))+1           
            for x in range( 0, self.panel_rows):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset+x)*self._bpp+idx_color] = buf[(y*self.max_x+x+self.panel_cols)*self._bpp+idx_color]

    def _transfer_panel3(self, buf:bytearray, matrix:bytearray):
        # panel 3 (lower left) even rows
        for y in range( 0, self.panel_rows, 2):
            target_pixel_row_offset = self.panel_rows*(y+1) - 1
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset-x)*self._bpp+idx_color] = buf[((y+self.panel_rows)*self.max_x+x)*self._bpp+idx_color]

        # panel 3 (lower left) odd rows
        for y in range( 1, self.panel_rows + 1, 2):
            target_pixel_row_offset = self.panel_rows*y
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset+x)*self._bpp+idx_color] = buf[((y+self.panel_rows)*self.max_x+x)*self._bpp+idx_color]


    def _transfer_panel4(self, buf:bytearray, matrix:bytearray):
        # panel 4 (lower right) even rows
        for y in range( 0, self.panel_rows, 2):
            target_pixel_row_offset = (self.pixels_per_panel*2) - (self.panel_rows*(y))-1
            print( "target_pixel_row_offset: {}".format(target_pixel_row_offset) )
            for x in range( 0, self.panel_rows):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset-x)*self._bpp+idx_color] = buf[((y+self.panel_rows)*self.max_x+x+self.panel_cols)*self._bpp+idx_color]

        # panel 4 (lower right) odd rows        
        for y in range( 1, self.panel_rows + 1, 2):
            target_pixel_row_offset = (self.pixels_per_panel*2) - (self.panel_rows*(y+1))
            for x in range( 0, self.panel_rows):
                for idx_color in range (0,self._bpp):
                    matrix[(target_pixel_row_offset+x)*self._bpp+idx_color] = buf[((y+self.panel_rows)*self.max_x+x+self.panel_cols)*self._bpp+idx_color]

    def _transmit(self, buf:bytearray):
        if self.matrix is None:
            self.matrix = buf.copy()
                
        self.debug_buf( buf )
        
        source_x = 0
        source_y = 0

        
        self._transfer_panel1(buf, self.matrix)    
        self._transfer_panel2(buf, self.matrix)
        self._transfer_panel3(buf, self.matrix)
        self._transfer_panel4(buf, self.matrix)

        if False:
            # panel 1 first 16 pixel of one row
            start_x = source_x
            start_y = source_y
            target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + self.panel_rows
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    self.matrix[(target_pixel_row_offset-x)*self._bpp+idx_color] = buf[x*self._bpp+idx_color]
            


            # panel 1 second row
            start_x = 0
            start_y += 1
            target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + (self.panel_rows*(start_y))+1
            for x in range( 0, self.panel_rows ):
                for idx_color in range (0,self._bpp):
                    self.matrix[(target_pixel_row_offset+x)*self._bpp+idx_color] = buf[(start_y*self.max_x+x)*self._bpp+idx_color]


        if False:
            # odd rows of the upper left panel
            for current_row in range( 0, self.panel_rows, 2 ):
                target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + self.panel_rows * (current_row + 1)
                for i in range( 0, self.panel_rows ):
                    for idx_color in range (0,self._bpp):
                        self.matrix[(target_pixel_row_offset-i)*self._bpp+idx_color] = buf[i+(current_row*self.panel_rows)*self._bpp+idx_color]

        if False:
            current_row = 1
            target_pixel_row_offset = self.max_pixel_offset - self.pixels_per_panel + self.panel_rows * (current_row + 2)
            for i in range( 0, self.panel_rows ):
                print( (target_pixel_row_offset+i) )
                for idx_color in range (0,self._bpp):                
                    self.matrix[(target_pixel_row_offset+i)*self._bpp+idx_color] = buf[i*self._bpp+idx_color]


        #self.matrix[0] = 255
        # self.matrix[768:168+16] = buf[0:16].reverse()
        return super()._transmit(self.matrix)
    
    def debug_buf( self, buf:bytearray):
        print( "buffer:" )
        for y in range( 0, self.max_y):
            line = ""
            for x in range( 0, self.max_x):
                offset = y*self.max_x + x
                if buf[offset*self._bpp+0] > 0 or buf[offset*self._bpp+1] > 0 or buf[offset*self._bpp+2] > 0:
                    line += "X"
                else:
                    line += " "
            print( "'{}'".format(line) )



#pixels = Pi5Pixelbuf(NEOPIXEL, num_pixels, auto_write=True, byteorder="GRB", brightness=0.2)
pixels = PixelBufLEDMatrix(NEOPIXEL, num_pixels, auto_write=True, byteorder="GRB", brightness=0.2)

rainbow = Rainbow(pixels, speed=0.02, period=2)
rainbow_chase = RainbowChase(pixels, speed=0.02, size=5, spacing=3)
rainbow_comet = RainbowComet(pixels, speed=0.02, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixels, speed=0.02, num_sparkles=15)




animations = AnimationSequence(
    rainbow,
    rainbow_chase,
    rainbow_comet,
    rainbow_sparkle,
    advance_interval=50,
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
        draw__1(0,pixels)
        draw__2(16*2,pixels)
        draw_filled_circle(16, 16, 14, pixels, color=(0, 255, 0))
        pixels.show()        
        break
        #animations.animate()
finally:
    time.sleep(.02)
    #pixels.fill(0)
    #pixels.show()
