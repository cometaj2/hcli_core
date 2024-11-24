#!/bin/bash

# monitor the default channel for activity and play the stream if the channel is active.
while :
do
    status=`curl 'https://hcli.io/hcli/cli/exec/getexecute?command=hptt%20channel%20ptt%20%27default%27'`
    if [[ "$status" == "active" ]]
    then
        hptt channel stream -r 'default' | sox -v 10.0 --ignore-length -t wav - -t wav - | play -
    fi

    sleep 1
done
