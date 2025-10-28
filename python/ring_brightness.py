import fog
import os;
from time import sleep 
import gpiod
import os
import sys
from config import Config
import GpiodBase

class Ring(GpiodBase.GpiodBase):
    
    PIN_NAME = "GPIO23"
    chip = ""
    offset = 0
    config = {}
    is_ringing = False
     
    def __init__(self, gpio_pin:str):
        super().__init__()
        self.PIN_NAME = gpio_pin
        (self.chip,self.offset) = self.find_line_by_name(self.PIN_NAME)
        self.config={ self.offset: gpiod.LineSettings( direction=gpiod.line.Direction.INPUT ) }
        self.request = gpiod.request_lines( self.chip, config=self.config )

    def detect_ringing(self):
        val = self.request.get_value(self.offset)
        #print("RING: {}".format(val))

        if val == gpiod.line.Value.ACTIVE:
            print("RINGING")
            self.is_ringing = True

    def adjust_brightness( self ):
        config = Config()
        brightness = config.get('brightness')

        if brightness == None:
            return

        brightness = float(brightness)

        
        brightness += 0.1

        if brightness > 0.8:
            brightness = 0.02

        print( "brightness: {0}".format( str(brightness) ) )                    
        config.put('brightness',str(brightness))

                                
    def run(self):
        while True:            
            self.detect_ringing()
            
            if self.is_ringing:
                self.adjust_brightness()
                sleep(0.3)
                
            self.is_ringing = False
            sleep(0.05)


#PIN = 16
#PIN = 1
#PIN = 7
#PIN = 8
#PIN = 25

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: {} <GPIO_PIN_NAME> [GPIO1,GPIO7,GPIO8,GPIO16,GPIO25]\n".format(sys.argv[0]))
        sys.exit(1)

    ring = Ring( sys.argv[1] )
    ring.run()