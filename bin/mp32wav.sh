#!/usr/bin/env bash

for i in *.mp3; do
  if ! test -f "${i%mp3}wav" ; then
	  ffmpeg -t 15 -i "$i" -acodec pcm_s16le -af "afade=type=out:start_time=13:duration=2" "${i%mp3}wav"
  fi	  
done
