#!/usr/bin/python
import MySQLdb
import configparser
import sys
import os

class Config:

    def __init__(self):
        config = configparser.ConfigParser()      
        r = config.read( os.getenv("HOME") + "/.UselessPope-Broker.ini" )

        print(r)

        username = config.get('database', 'username')
        password = config.get('database', 'password')
        instance = config.get('database', 'instance')

        self.db = MySQLdb.connect(host="localhost",                 # your host, usually localhost
                                  user=username,    # your username
                                  passwd=password,  # your password
                                  db=instance)        # name of the data base
        
    def get( self, key: str ):
        cursor = self.db.cursor()

        cursor.execute( "select `value` from `CONFIG` where `key`='{0}'".format( key ) )

        for row in cursor.fetchall():
            return row[0]

        return None

    
if __name__ == "__main__":
    config = Config()   

    brightness = config.get("brightness")

    print( "brightness: {0}".format( brightness) )