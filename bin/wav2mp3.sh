#!/usr/bin/env bash

for i in *.WAV; do
  if ! test -f "${i%WAV}mp3" ; then
	  ffmpeg -i "$i" "${i%wav}mp3"
  fi	  
done
