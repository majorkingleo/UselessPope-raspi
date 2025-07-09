#!/usr/bin/env bash

for i in *.ogg; do
  ffmpeg -acodec libvorbis -i "$i" -acodec pcm_s16le "${i%ogg}wav"
done
