#!/bin/bash

while :
do
    arecord -N -D plughw:1,0 -d 1 -f S16_LE > sample.wav
    status=`sox -t .wav sample.wav -n stat 2>&1 | awk '/^RMS     amplitude/ { print $3 < .000300 ? "inactive" : "active" }'`
    if [[ "$status" == "active" ]]
    then
       arecord -N -D hw:1,0 -f S16_LE -c1 -r44100 | hptt channel stream -l 'default'
    fi
done
