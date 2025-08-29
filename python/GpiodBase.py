import gpiod
import gpiod.line
import os

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

