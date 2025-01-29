import subprocess
import os
import pytest

def test_success_hco_key_admin_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco key admin
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

def test_success_hco_ls_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin' in result)

def test_success_jsonf_go_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo -n '{"hello":"world"}' | jsonf go
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('{\n    "hello": "world"\n}' in result)

def test_success_hco_useradd_newuser_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco useradd newuser
    hco ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin    admin\nnewuser    user' == result)

def test_success_hco_userdel_newuser_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco userdel newuser
    hco ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin    admin' == result)

def test_success_hco_useradd_hello_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco useradd hello
    hco ls
    echo 'yehaw' | hco passwd hello

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin    admin\nhello    user' == result)

def test_success_hco_validate_basic_hello_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo 'yehaw' | hco validate basic hello

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('valid' == result)

def test_error_hco_validate_basic_hello_as_hello(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo 'yehaw' | huckle cli credential hco hello
    huckle cli config hco auth.user.profile username_profile1
    echo 'yehaw' | hco validate basic hello

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert('hcli_core: hello has insufficient permissions to execute hco validate basic "hello"\n' == error)

def test_error_hco_ls_as_hello(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco ls

    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert ('hcli_core: hello has insufficient permissions to execute hco ls\n' in error)

def test_error_hco_useradd_yehaw_as_hello(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco useradd yehaw
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert ('hcli_core: hello has insufficient permissions to execute hco useradd "yehaw"\n' in error)

def test_error_hco_userdel_hello_as_hello(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco userdel hello
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert ('hcli_core: hello has insufficient permissions to execute hco userdel "hello"\n' in error)
