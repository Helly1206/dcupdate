#!/usr/bin/bash

# -*- coding: utf-8 -*-
#########################################################
# SCRIPT : doupdate.sh                                  #
#          update docker-compose stack from commandline #
#          Simple app to send commands to socket        #
#          I. Helwegen 2024                             #
#########################################################

echo $1 > /dev/tcp/127.0.0.1/65432