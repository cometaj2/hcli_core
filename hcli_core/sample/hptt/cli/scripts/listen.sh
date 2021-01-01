#!/bin/bash

while :
do
    arecord -D plughw:1,0 -d 1 -f S16_LE > sample.wav
    status=`sox -t wav sample.wav -n stat 2>&1 | awk '/^RMS     amplitude/ { print $3 < .000300 ? "inactive" : "active" }'`
    if [[ "$status" == "active" ]]
    then
       cvlc -vvv alsa://hw:1,0 --sout '#standard{access=file,mux=wav,dst=-}' vlc:quit |
       hptt channel stream -l 'default'
    fi
done
