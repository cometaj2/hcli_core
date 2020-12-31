#!/bin/bash

while :
do
    status=`curl 'https://hcli.io/hcli/cli/exec/getexecute?command=hptt%20channel%20ptt%20%27default%27'`
    if [[ "$status" == "active" ]]
    then
        curl 'https://hcli.io/hcli/cli/exec/getexecute?command=hptt%20channel%20stream%20-r%20%27default%27' | aplay
    fi
    
    sleep 1
done
