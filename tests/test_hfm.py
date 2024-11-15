import subprocess
import os
import pytest

def test_function():
    setup = """
    #!/bin/bash
    set -x

    # we setup a custom credentials file for the test run
    echo -e "[config]
core.auth = False" > ./test_credentials

    gunicorn --workers=1 --threads=1 -b 0.0.0.0:8000 "hcli_core:connector(plugin_path=\\\"`hcli_core sample hfm`\\\", config_path=\\\"./test_credentials\\\")" --daemon

    huckle cli install http://127.0.0.1:8000

    echo "Debug checks post-install..."
    cat ~/.huckle/etc/hfm/config
    """

    p1 = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p1.communicate()


    if out is not None:
        print(f"STDOUT: {out}")

    if err is not None:
        print(f"STDERR: {err}")

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

    if err is not None:
        print(f"STDERR: {err}")

    assert(result == '{"hello":"world"}\n')

