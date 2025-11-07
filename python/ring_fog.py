import fog
import os;
from time import sleep 
import gpiod
import os
import sys
import config
from config import Config
import time

class Ring (fog.Fog):    
    
    PIN_NAME = "GPIO23"
    chip = ""
    offset = 0
    config = {}
    tone_dir = "/home/papst/mp3/Soundboard/_sounds"
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
                                
    def run(self):

        config_refresh_time_out = 0
        config = Config()
        old_fog_state = 0        

        while True:
            # refresh brightness if changed
            if time.time() > config_refresh_time_out:
                config_refresh_time_out = time.time() + 0.5
                fog = config.get('fog')

                if fog != None and fog != old_fog_state:
                    self.toggle()
                    old_fog_state = fog

            self.detect_ringing()
            
            if self.is_ringing:
                self.toggle()
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

    # wait for database to start
    while not config.is_db_available():
        time.sleep(0.3)

    ring = Ring( sys.argv[1] )
    ring.run()