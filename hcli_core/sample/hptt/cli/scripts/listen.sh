#!/bin/bash

# define signal handler and its variable
allowAbort=true;
myInterruptHandler()
{
    if $allowAbort; then
        exit 1;
    fi;
}

# register signal handler
trap myInterruptHandler SIGINT;

# continuously monitor ffmpeg silence log and terminate cvlc if a long enough silence is detected
silence(){
while :
do
    silence="0"
    if [[ -f "silence.log" ]]
    then
	silence=`cat silence.log |
        grep -Eo "silence_(start|end)" |
        tail -n 1 |
        grep "start" |
        wc -l`
    fi

    if [[ "$silence" == "1" ]]
        then
        pid=`ps -ef | grep "/usr/bin/[v]lc -I dummy -vvv alsa://hw:1,0 --sout #standard{access=file,mux=wav,dst=-} vlc:quit" |
        awk '{print $2}'`

        kill -9 $pid
        rm silence.log
    fi
done
}

# Check for sound, then record and monitor for silence while streaming to the hptt service without blocking.
# We have a background process that continuously monitors for the silence log to kill cvlc if a long enough silence is detected.
# Fine tune the negative noise level to help establish the silence floor you want to trigger silence detection on.
# You can also fine tune the duration d on ffmpeg to change the trigger for silence detection.
silence &

while :
do
    arecord -D plughw:1,0 -d 1 -f S16_LE > sample.wav
    status=`sox -t wav sample.wav -n stat 2>&1 | awk '/^RMS     amplitude/ { print $3 < .000300 ? "inactive" : "active" }'`
    if [[ "$status" == "active" ]]
    then
       cvlc -vvv alsa://hw:1,0 --sout '#standard{access=file,mux=wav,dst=-}' vlc:quit |
       ffmpeg -i - -af silencedetect=n=-70dB:d=3 -f wav - 2> silence.log |
       hptt channel stream -l 'default'
    fi
done
