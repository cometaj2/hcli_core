import subprocess
import os
import pytest

def test_hco_key_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco key admin

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    key_id, api_key, timestamp = result.split()

    # Expected lengths based on your example
    assert len(key_id) == 10, f"Key ID length should be 10, got {len(key_id)}"
    assert len(api_key) == 92, f"API key length should be 107, got {len(api_key)}"
    assert len(timestamp) == 32, f"Timestamp length should be 32, got {len(timestamp)}"

    # Verify format patterns
    assert key_id.isalnum(), "Key ID should be alphanumeric"
    assert api_key.startswith("hcoak_"), "API key should start with 'hcoak_'"

def test_hco_ls(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco ls

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin' in result)

def test_jsonf(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo '{"hello":"world"}' | jsonf go
    kill $(ps aux | grep '[g]unicorn' | awk '{print $2}')
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('{\n    "hello": "world"\n}' in result)

