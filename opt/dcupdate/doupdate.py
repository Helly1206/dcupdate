#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SCRIPT : doupdate.py                                  #
#          update docker-compose stack from commandline #
#          Simple app to send commands to socket        #
#          I. Helwegen 2024                             #
#########################################################

####################### IMPORTS #########################
import sys
import socket

#########################################################

####################### GLOBALS #########################

APP_NAME = "doupdate"
VERSION = "0.80"
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
#########################################################

######################### MAIN ##########################
if __name__ == "__main__":
    #print("{} app, version {}".format(APP_NAME, VERSION))
    cmd = ""
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(cmd.encode('utf-8'))