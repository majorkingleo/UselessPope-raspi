import adafruit_pixelbuf

from adafruit_raspberry_pi5_neopixel_write import neopixel_write

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

    
class LEDMatrix(Pi5Pixelbuf):
    
    panel_rows = 16
    panel_cols = 16    
    panels = 4
    matrix = bytearray(panel_rows*panel_cols*panels * 3)  # 3 bytes per pixel
    pixels_per_panel = panel_rows*panel_cols    
    max_pixel_offset = pixels_per_panel * panels - 1 # 1024
    max_x = panel_cols*2
    max_y = panel_rows*2

    def __init__(self, pin, **kwargs):        
        super().__init__(pin, self.panel_rows*self.panel_cols*self.panels, byteorder="GRB", **kwargs)

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
        #if self.matrix is None:
        #    self.matrix = buf.copy()
        
        self._transfer_panel1(buf, self.matrix)    
        self._transfer_panel2(buf, self.matrix)
        self._transfer_panel3(buf, self.matrix)
        self._transfer_panel4(buf, self.matrix)
       
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

                    