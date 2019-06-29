from __future__ import absolute_import, division, print_function

import subprocess
import os

def test_function():
    setup = """
    #!/bin/bash

    cd `hcli_core path`
    gunicorn --workers=5 --threads=2 --chdir `hcli_core path` "hcli_core:HCLI(\"`hcli_core sample hfm`\").connector"
    huckle cli install http://127.0.0.1:8000
    echo '{"hello":"world"}' > hello.json
    """

    p1 = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p1.communicate()

    hello = """
    #!/bin/bash

    export PATH=$PATH:~/.huckle/bin
    cat hello.json | rsm cp -l "./hello1.json"
    diff hello.json hello1.json
    """
    
    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('' in result)
