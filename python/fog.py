#!/usr/bin/python


import os
import sys
import time
import GpiodBase
import gpiod

class Fog (GpiodBase.GpiodBase):    
    
    Fog_PIN_NAME = "GPIO23"
    Fog_chip = ""
    Fog_offset = 0
    Fog_config = {}
     
    def __init__(self):
        (self.Fog_chip,self.Fog_offset) = self.find_line_by_name(self.Fog_PIN_NAME)
        self.Fog_config={ self.Fog_offset: gpiod.LineSettings( direction=gpiod.line.Direction.OUTPUT )}
        self.Fog_request = gpiod.request_lines( self.Fog_chip, config=self.Fog_config )            

    def on(self):
        self.Fog_request.set_value( self.Fog_offset, gpiod.line.Value.ACTIVE )
        print("Fog ON")
        
    def off(self):
        self.Fog_request.set_value( self.Fog_offset, gpiod.line.Value.INACTIVE )
        print("Fog OFF")

    def toggle(self):
        current_value = self.Fog_request.get_value(self.Fog_offset)
        if current_value == gpiod.line.Value.ACTIVE:
            self.off()
            return 0
        else:
            self.on()
            return 1

if __name__ == "__main__":
    fog = Fog()
    if len(sys.argv) > 1 and ( sys.argv[1] == "on" or sys.argv[1] == "1" ):
        fog.on()
    elif len(sys.argv) > 1 and ( sys.argv[1] == "off" or sys.argv[1] == "0" ):
        fog.off()
    else:
        fog.toggle()

    time.sleep(5)
