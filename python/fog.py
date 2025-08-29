#!/usr/bin/python


import os
import sys
import time
import GpiodBase
import gpiod

class Fog (GpiodBase.GpiodBase):    
    
    PIN_NAME = "GPIO23"
    chip = ""
    offset = 0
    config = {}
     
    def __init__(self):
        (self.chip,self.offset) = self.find_line_by_name(self.PIN_NAME)
        self.config={ self.offset: gpiod.LineSettings( direction=gpiod.line.Direction.OUTPUT )}
        self.request = gpiod.request_lines( self.chip, config=self.config )            

    def on(self):
        self.request.set_value( self.offset, gpiod.line.Value.ACTIVE )
        print("Fog ON")
        
    def off(self):
        self.request.set_value( self.offset, gpiod.line.Value.INACTIVE )
        print("Fog OFF")

    def toggle(self):
        current_value = self.request.get_value(self.offset)
        if current_value == gpiod.line.Value.ACTIVE:
            self.off()
        else:
            self.on()

if __name__ == "__main__":
    fog = Fog()
    if len(sys.argv) > 1 and ( sys.argv[1] == "on" or sys.argv[1] == "1" ):
        fog.on()
    elif len(sys.argv) > 1 and ( sys.argv[1] == "off" or sys.argv[1] == "0" ):
        fog.off()
    else:
        fog.toggle()

    time.sleep(5)
