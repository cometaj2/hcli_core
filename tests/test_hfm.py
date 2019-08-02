from __future__ import absolute_import, division, print_function

import subprocess
import os

def test_function():
    setup = """
    #!/bin/bash
    set -x

    gunicorn --workers=1 --threads=1 --chdir `hcli_core path` "hcli_core:HCLI(\\"`hcli_core sample hfm`\\").connector" --daemon
    huckle cli install http://127.0.0.1:8000
    """

    p1 = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p1.communicate()

    hello = """
    #!/bin/bash
    set -x

    export PATH=$PATH:~/.huckle/bin
    echo '{"hello":"world"}' > hello.json
    cat hello.json | hfm cp -l ./hello.json
    hfm cp -r hello.json > hello1.json
    kill $(ps aux | grep '[g]unicorn' | awk '{print $2}')
    cat hello1.json
    rm hello.json
    rm hello1.json
    """
    
    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert(result == '{"hello":"world"}\n')

