import sys
import os
import json
import hashlib
import threading
from configparser import ConfigParser
from hcli_core import logger
from hcli_core import config

log = logger.Logger("hcli_core")


class CredentialManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._credentials = None
        self.parse_configuration()

    @property
    def credentials(self):
        with self._lock:
            return self._credentials

    @credentials.setter
    def credentials(self, value):
        with self._lock:
            self._credentials = value

    # parses credentials configuration
    def parse_configuration(self):
        auth = config.auth

        try:
            parser = ConfigParser()
            parser.read(config.config_file_path)
            if parser.has_section("config"):
                for section_name in parser.sections():
                    if section_name == "config":
                        log.info("[" + section_name + "]")
                        for name, value in parser.items("config"):
                            if name == "authenticate":
                                if value != "False" and value != "True":
                                    log.warning("Unsuported authentication value: " + str(value) + ". Disabling authentication.")
                                    config.auth = False
                                    log.info("Authenticate: " + str(config.auth))
                                else:
                                    auth = value
                                    if value.lower() == 'true':
                                        config.auth = True
                                    elif value.lower() == 'false':
                                        config.auth = False
                                    log.info("Authenticate: " + str(config.auth))
            else:
                log.critical("No [config] configuration available for " + config.config_file_path + ".")
                assert isinstance(auth, str)
        except:
            log.critical("Unable to load configuration.")
            assert isinstance(auth, str)

    def parse_credentials(self):
        with self._lock:
            try:
                parser = ConfigParser()
                log.info("Loading credentials")
                log.info(config.config_file_path)
                parser.read(config.config_file_path)

                # Check if we have a default section for the admin user
                if not parser.has_section("default"):
                    log.critical(f"No [default] credential available for {config.config_file_path}.")
                    self._credentials = None
                    assert isinstance(self._credentials, dict)
                    return False

                # Check if we have a default admin username and password
                if not parser.has_option("default", "username") or parser.get("default", "username") != "admin" or not parser.has_option("default", "password"):
                    log.critical(f"Invalid or missing admin username or password in [default] section of {config.config_file_path}.")
                    self._credentials = None
                    assert isinstance(self._credentials, dict)
                    return False

                # Check for unique usernames across all sections
                usernames = set()
                for section in parser.sections():
                    if parser.has_option(section, "username"):
                        username = parser.get(section, "username")
                        if username in usernames:
                            log.critical(f"Duplicate username '{username}' found in {config.config_file_path}.")
                            self._credentials = None
                            assert isinstance(self._credentials, dict)
                            return False
                        usernames.add(username)

                new_credentials = {}
                for section_name in parser.sections():
                    new_credentials[str(section_name)] = []
                    for name, value in parser.items(section_name):
                        new_credentials[str(section_name)].append({str(name): str(value)})

                self._credentials = new_credentials
                return True

            except Exception as e:
                log.critical(f"Unable to load credentials: {str(e)}.")
                self._credentials = None
                assert isinstance(self._credentials, dict)
                return False

    def validate(self, username, password):
        with self._lock:
            try:
                if not self._credentials:
                    return False

                for section, cred_list in self._credentials.items():
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

            except Exception as e:
                log.error(f"Error validating credentials: {str(e)}.")
                return False

    @property
    def is_loaded(self):
        with self._lock:
            return self._credentials is not None
