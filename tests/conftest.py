import subprocess
import os
import pytest

# bootstrap the test by starting an hcli server with mgmt config and fresh * admin creds
@pytest.fixture(scope="module")
def gunicorn_server_auth():
    # Start gunicorn server
    setup = """
    #!/bin/bash
    set -x
    export PATH=$PATH:~/.huckle/bin

    echo "Cleanup preexisting huckle hcli installations..."
    huckle cli rm hco
    huckle cli rm jsonf
    huckle cli rm hfm

    echo "Cleanup old run data..."
    rm -f ./gunicorn-error.log
    rm -f ./test_credentials
    rm -f ./password

    echo "Setup a custom credentials file for the test run"
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

    echo "Setup bootstrap admin config and credentials for hco and jsonf..."
    echo -e "[default]
username = admin
password = `cat ./password`" > ~/.huckle/etc/hco/credentials

    echo -e "[default]
username = admin
password = `cat ./password`" > ~/.huckle/etc/jsonf/credentials

    echo "Setting up basic auth config..."
    sed -i.backup 's/auth.mode = skip/auth.mode = basic/' ~/.huckle/etc/hco/config
    sed -i.backup 's/auth.mode = skip/auth.mode = basic/' ~/.huckle/etc/jsonf/config

    echo "Validating config files..."
    grep "auth.mode" ~/.huckle/etc/hco/config
    grep "auth.mode" ~/.huckle/etc/jsonf/config

    """
    process = subprocess.Popen(['bash', '-c', setup], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = process.communicate()

    # Verify setup worked
    assert os.path.exists('./gunicorn-error.log'), "gunicorn-error.log not found"
    assert os.path.exists('./test_credentials'), "test_credentials not found"
    assert os.path.exists('./password'), "password not found"

@pytest.fixture(scope="module")
def cleanup():

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
    if os.path.exists('./gunicorn-noauth-error.log'):
        os.remove('./gunicorn-noauth-error.log')
    if os.path.exists('./test_credentials'):
        os.remove('./test_credentials')
    if os.path.exists('./noauth_credentials'):
        os.remove('./noauth_credentials')
    if os.path.exists('./password'):
        os.remove('./password')
    if os.path.exists('./test_credentials.lock'):
        os.remove('./test_credentials.lock')
    if os.path.exists('./noauth_credentials.lock'):
        os.remove('./noauth_credentials.lock')

    # Verify files are gone
    assert not os.path.exists('./gunicorn-error.log'), "gunicorn-error.log still exists"
    assert not os.path.exists('./gunicorn-noauth-error.log'), "gunicorn-noauth-error.log still exists"
    assert not os.path.exists('./test_credentials'), "test_credentials still exists"
    assert not os.path.exists('./test_credentials.lock'), "test_credentials.lock still exists"
    assert not os.path.exists('./noauth_credentials'), "test_credentials still exists"
    assert not os.path.exists('./noauth_credentials.lock'), "noauth_credentials.lock file still exists"
    assert not os.path.exists('./password'), "password still exists"
