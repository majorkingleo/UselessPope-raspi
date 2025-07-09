#!/usr/bin/python

import RPi.GPIO as GPIO
import os;
import random;
from time import sleep 

class Ring:
    
    is_ringing = False
    PIN = 18
    tone_dir = "/home/user/mp3/ring"
    
    def __init__(self):
        GPIO.setmode(GPIO.BCM);
        GPIO.setup( self.PIN, GPIO.IN)

    def detect_ringing(self):
        if GPIO.input(self.PIN) == 1:
            self.is_ringing = True
                
    def play_sound(self):
        files = list()
        for f in os.listdir(self.tone_dir):
            if f.endswith(".wav"):
                files.append(f)
            
        random.shuffle(files)
                
        os.system( "aplay ~/mp3/ring/" + files[0] );
        #os.system( "mplayer ~/mp3/ring/" + files[0] );
        #os.system( "%s%s".format("mplayer ~/mp3/ring/",files[0]) );
                
    def run(self):
        while True:            
            self.detect_ringing()
            
            if self.is_ringing:
                self.play_sound()
                
            self.is_ringing = False
            sleep(0.05)


ring = Ring()
ring.run();

