import subprocess
import os
import pytest

def test_hco_key_admin_as_admin(gunicorn_server_auth, cleanup):
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

    hello = f"""
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    sleep 0.1

    hco key rotate {key_id}
    """
    p3 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p3.communicate()
    result = out.decode('utf-8')

    rotated_key_id, rotated_api_key, rotated_timestamp = result.split()

    # Expected lengths based on your example
    assert len(rotated_key_id) == 10, f"Key ID length should be 10, got {len(key_id)}"
    assert len(rotated_api_key) == 92, f"API key length should be 107, got {len(api_key)}"
    assert len(rotated_timestamp) == 32, f"Timestamp length should be 32, got {len(timestamp)}"

    # Verify format patterns
    assert rotated_key_id.isalnum(), "Key ID should be alphanumeric"
    assert rotated_api_key.startswith("hcoak_"), "API key should start with 'hcoak_'"

    # Check to see if we have rotation on same key_id
    assert key_id == rotated_key_id
    assert api_key != rotated_key_id
    assert timestamp != rotated_timestamp

    hello = f"""
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco key rm {key_id}
    """
    p4 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p4.communicate()

    assert p4.returncode == 0

    hello = f"""
    #!/bin/bash
    set -x

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco key rm {key_id}
    """
    p5 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p5.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert f"api key {key_id} not found.\n" in error

def test_hco_ls_as_admin(gunicorn_server_auth, cleanup):
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

def test_jsonf_go_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo -n '{"hello":"world"}' | jsonf go
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('{\n    "hello": "world"\n}\n' in result)

def test_hco_useradd_newuser_as_admin(gunicorn_server_auth, cleanup):
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

    assert('admin\nnewuser\n' == result)

def test_hco_userdel_newuser_as_admin(gunicorn_server_auth, cleanup):
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

    assert('admin\n' == result)

def test_hco_useradd_hello_as_admin(gunicorn_server_auth, cleanup):
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

    assert('admin\nhello\n' == result)

def test_hco_validate_basic_hello_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    echo 'yehaw' | hco validate basic hello
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('valid\n' == result)

def test_hco_role_ls_as_admin(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco role ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')

    assert('admin    admin\n' in result)

def test_hco_validate_basic_hello_as_hello_user_role(gunicorn_server_auth, cleanup):
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

    assert('hello has insufficient permissions to execute hco validate basic "hello"\n' == error)

def test_hco_ls_as_hello_user(gunicorn_server_auth, cleanup):
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

    assert ('hello has insufficient permissions to execute hco ls\n' in error)

def test_hco_useradd_yehaw_as_hello_user_role(gunicorn_server_auth, cleanup):
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

    assert ('hello has insufficient permissions to execute hco useradd "yehaw"\n' in error)

def test_hco_userdel_hello_as_hello_user_role(gunicorn_server_auth, cleanup):
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

    assert ('hello has insufficient permissions to execute hco userdel "hello"\n' in error)










def test_hco_validate_basic_hello_as_hello_admin_role(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    huckle cli config hco auth.user.profile default
    hco role add hello admin
    huckle cli config hco auth.user.profile username_profile1
    echo 'yehaw' | hco validate basic hello
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert('valid\n' in result)

def test_hco_ls_as_hello_admin_role(gunicorn_server_auth, cleanup):
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

    assert ('admin\nhello\n' in result)

def test_hco_useradd_yehaw_as_hello_admin_role(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco useradd yehaw
    hco ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert ('admin\nhello\nyehaw\n' in result)

def test_hco_userdel_hello_as_hello_admin_role(gunicorn_server_auth, cleanup):
    hello = """
    #!/bin/bash

    export HUCKLE_HOME=~/.huckle_test
    eval $(huckle env)

    hco userdel hello
    huckle cli config hco auth.user.profile default
    hco ls
    """

    p2 = subprocess.Popen(['bash', '-c', hello], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    result = out.decode('utf-8')
    error = err.decode('utf-8')

    assert ('admin\nyehaw\n' in result)
