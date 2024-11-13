import subprocess
import os
import pytest

# bootstrap the test by starting an hcli server with mgmt config and fresh * admin creds
@pytest.fixture(scope="session")
def gunicorn_server():
    # Start gunicorn server
    setup = """
    #!/bin/bash
    set -x
    export PATH=$PATH:~/.huckle/bin

    # cleanup old run data
    rm -f ./gunicorn-error.log
    rm -f ./test_credentials
    rm -f ./password

    # we setup a custom credentials file for the test run
    echo -e "[config]
core.auth = True
mgmt.port = 9000

[default]
username = admin
password = *
salt = *" > ./test_credentials

    gunicorn --workers=1 --threads=1 -b 0.0.0.0:8000 -b 0.0.0.0:9000 "hcli_core:connector(config_path=\\\"./test_credentials\\\")" --daemon --log-file=./gunicorn.log --error-logfile=./gunicorn-error.log --capture-output

    sleep 2

    grep "Password:" ./gunicorn-error.log | awk '{print $8}' > ./password
    huckle cli install http://127.0.0.1:8000
    huckle cli install http://127.0.0.1:9000

    echo -e "[default]
username = admin
password = `cat ./password`" > ~/.huckle/etc/hco/credentials

    echo -e "[default]
username = admin
password = `cat ./password`" > ~/.huckle/etc/jsonf/credentials
    """
    process = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = process.communicate()

    # Verify setup worked
    assert os.path.exists('./gunicorn-error.log'), "gunicorn-error.log not found"
    assert os.path.exists('./test_credentials'), "test_credentials not found"
    assert os.path.exists('./password'), "password not found"

    # Let the tests run
    yield

    # Enhanced cleanup with verification
    cleanup_script = """
    #!/bin/bash
    set -x  # Print commands as they execute

    # Force kill any remaining processes
    for pid in $(ps aux | grep '[g]unicorn' | awk '{print $2}'); do
        kill -9 $pid 2>/dev/null || true
    done
    """

    # Run cleanup and capture output
    cleanup_process = subprocess.run(['bash', '-c', cleanup_script], capture_output=True, text=True)

    # One final check with Python's os module
    if os.path.exists('./gunicorn-error.log'):
        os.remove('./gunicorn-error.log')
    if os.path.exists('./test_credentials'):
        os.remove('./test_credentials')
    if os.path.exists('./password'):
        os.remove('./password')

    # Verify files are gone
    assert not os.path.exists('./gunicorn-error.log'), "gunicorn-error.log still exists"
    assert not os.path.exists('./test_credentials'), "test_credentials still exists"
    assert not os.path.exists('./password'), "password still exists"

# generate an api key with the bootstrapped admin password
def test_hco_key_admin(gunicorn_server):
    hello = """
    #!/bin/bash
    set -x

    export PATH=$PATH:~/.huckle/bin
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
