import subprocess
import os
import pytest

def test_jsonf(gunicorn_server):
    hello = """
    #!/bin/bash

    export PATH=$PATH:~/.huckle/bin
    echo '{"hello":"world"}' | jsonf go
    kill $(ps aux | grep '[g]unicorn' | awk '{print $2}')
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('{\n    "hello": "world"\n}\n' in result)

