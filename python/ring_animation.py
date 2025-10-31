import fog
import os;
from time import sleep 
import gpiod
import os
import sys
from config import Config
import GpiodBase

class Ring(GpiodBase.GpiodBase):
    
    PIN_NAME = "GPIO24"
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

    def next_animation( self ):
        config = Config()
        animation = config.get('current_animation')

        if animation == None:
            animation = 0

        animation = int(animation)+1

        animation_file = config.get("animation{0}".format(animation))
        if animation_file == None:
            animation = 0
            animation_file = config.get("animation{0}".format(animation))

        assert animation_file != None
    
        config.put('current_animation',str(animation))

        print( "Playing animation file: {}".format( animation_file ) )

        cursor = config.db.cursor()
        cursor.execute( "insert into PLAY_QUEUE_ANIMATION( hist_an_user, hist_ae_user, hist_lo_user, file ) " \
                        "values( 'papst', 'papst', 'papst', '{0}' )".format( animation_file ) )
        cursor.execute( "commit" )

                                
    def run(self):
        while True:            
            self.detect_ringing()
            
            if self.is_ringing:
                self.next_animation()
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