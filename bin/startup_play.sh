#!/usr/bin/env bash

# Source - https://stackoverflow.com/a/2173421
# Posted by tokland, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-08, License - CC BY-SA 4.0

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

XDG_RUNTIME_DIR=/run/user/1000
BROKER=/home/papst/UselessPope-Broker/broker
POPE_FILE=/home/papst/UselessPope-Broker/papst_answers.txt

#sleep 3
#echo "starting"
#/usr/bin/aplay /home/papst/mp3/angel/*.wav
#echo "done"


while ! test -e /run/mysqld/mysqld.sock; do
	sleep 1
done

killall broker

${BROKER} -enqueue-music /home/papst/audio_music/*

${BROKER} -debug > /tmp/broker.log &
wait

