import sys
import os
import importlib
import json
import hashlib

from configparser import ConfigParser
from hcli_core import logger
from hcli_core import config

log = logger.Logger("hcli_core")

credentials = None

# parses the credentials file to set valid username and passwords
def parse_credentials():
    global default_config_file_path
    global config_file_path
    global credentials

    (head, tail) = os.path.split(config.config_file_path)
    credentials_file_path = os.path.join(head, "credentials")

    # hcli_core expects a default 'admin' section (at least one user) which should be the administrator
    try:
        parser = ConfigParser()
        log.info("Loading credentials")
        log.info(credentials_file_path)
        parser.read(credentials_file_path)

        credentials = {}
        if parser.has_section("default"):
            for section_name in parser.sections():
                credentials[str(section_name)] = []
                for name, value in parser.items(section_name):
                    credentials[str(section_name)].append({str(name):str(value)})
        else:
            log.critical("No [default] credential available for " + credentials_file_path)
            credentials = None
            assert isinstance(credentials, dict)

    except:
        log.critical("Unable to load credentials.")
        credentials = None
        assert isinstance(credentials, dict)

def validate(username, password):
    try:
        global credentials
        for section, cred_list in credentials.items():
            section_username = None
            section_password = None
            for cred in cred_list:
                if 'username' in cred:
                    section_username = cred['username']
                if 'password' in cred:
                    section_password = cred['password']

            hashed = hashlib.sha512(password.encode('utf-8')).hexdigest()

            if username == section_username and hashed == section_password:
                return True

        return False
    except:
        return False
