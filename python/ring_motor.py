#!/usr/bin/python

import os;
import random;
from time import sleep 
import GpiodBase
import gpiod
import os
import sys


class Ring (GpiodBase.GpiodBase):    
    
    PIN_NAME = "GPIO23"
    chip = ""
    offset = 0
    config = {}
    tone_dir = "/home/papst/audio_motor"
    broker = "/home/papst/UselessPope-Broker/broker"
    is_ringing = False
     
    def __init__(self, gpio_pin:str):
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
                
    def play_sound(self):
        files = list()
        for f in os.listdir(self.tone_dir):
                files.append(f)
            
        random.shuffle(files)
                
        os.system( "{} -enqueue-music {}/{}".format( self.broker, self.tone_dir, files[0]) );
                
    def run(self):
        while True:            
            self.detect_ringing()
            
            if self.is_ringing:
                self.play_sound()
                
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

    #if len(sys.argv) > 1 and ( sys.argv[1] == "on" or sys.argv[1] == "1" ):
    #    ring.on()
    #elif len(sys.argv) > 1 and ( sys.argv[1] == "off" or sys.argv[1] == "0" ):
    #    fog.off()
    #else:
    #    fog.toggle()

    #time.sleep(5)