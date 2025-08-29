#!/usr/bin/python

import gpiod
import gpiod.line
import os
import sys
import time

class GpiodBase:

    def generate_gpio_chips(self):
        for entry in os.scandir("/dev/"):
            if gpiod.is_gpiochip_device(entry.path):
                yield entry.path


    def find_line_by_name(self,line_name):
        # Names are not guaranteed unique, so this finds the first line with
        # the given name.
        for path in self.generate_gpio_chips():
            with gpiod.Chip(path) as chip:
                try:
                    offset = chip.line_offset_from_id(line_name)
                    print( "{}".format( chip.get_line_info(offset) ) )
                    print("{}: {} {}".format(line_name, chip.get_info().name, offset))
                    return (path,offset)
                except OSError:
                    # An OSError is raised if the name is not found.
                    continue

        print("line '{}' not found".format(line_name))
        raise RuntimeError("line '{}' not found".format(line_name))


class Fog (GpiodBase):    
    
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
