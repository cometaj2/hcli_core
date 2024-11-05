import sys
import os
import json
import hashlib
import threading
import portalocker
from configparser import ConfigParser

from hcli_core import logger
from hcli_core import config

from contextlib import suppress

log = logger.Logger("hcli_core")


class CredentialManager:
    def __init__(self):
        self._lock = threading.RLock()  # For thread safety within process
        self._credentials = None
        self.cfg = config.Config()
        self.parse_configuration()

    @property
    def credentials(self):
        with self._lock:
            return self._credentials

    @credentials.setter
    def credentials(self, value):
        with self._lock:
            self._credentials = value

    def parse_configuration(self):
        with self._lock:
            auth = self.cfg.auth

            try:
                # Use portalocker for file access
                with portalocker.Lock(self.cfg.config_file_path, 'r', timeout=10) as config_file:
                    parser = ConfigParser()
                    parser.read_file(config_file)

                    if parser.has_section("config"):
                        for section_name in parser.sections():
                            if section_name == "config":
                                log.info("[" + section_name + "]")
                                for name, value in parser.items("config"):
                                    if name == "authenticate":
                                        if value != "False" and value != "True":
                                            log.warning("Unsupported authentication value: " + str(value) + ". Disabling authentication.")
                                            self.cfg.auth = False
                                        else:
                                            if value.lower() == 'true':
                                                self.cfg.auth = True
                                            elif value.lower() == 'false':
                                                self.cfg.auth = False
                                        log.info("Authenticate: " + str(self.cfg.auth))
                    else:
                        log.critical("No [config] configuration available for " + self.cfg.config_file_path + ".")
                        assert isinstance(auth, str)
            except portalocker.LockTimeout:
                log.critical("Timeout waiting for config file lock.")
                assert isinstance(auth, str)
            except Exception as e:
                log.critical(f"Unable to load configuration: {str(e)}")
                assert isinstance(auth, str)

    def parse_credentials(self):
        with self._lock:
            try:
                # Use portalocker for file access
                with portalocker.Lock(self.cfg.config_file_path, 'r', timeout=10) as cred_file:
                    parser = ConfigParser()
                    log.info("Loading credentials")
                    log.info(self.cfg.config_file_path)
                    parser.read_file(cred_file)

                    # Check if we have a default section for the admin user
                    if not parser.has_section("default"):
                        log.critical(f"No [default] credential available for {self.cfg.config_file_path}.")
                        self._credentials = None
                        assert isinstance(self._credentials, dict)
                        return False

                    # Check if we have a default admin username and password
                    if not parser.has_option("default", "username") or parser.get("default", "username") != "admin" or not parser.has_option("default", "password"):
                        log.critical(f"Invalid or missing admin username or password in [default] section of {self.cfg.config_file_path}.")
                        self._credentials = None
                        assert isinstance(self._credentials, dict)
                        return False

                    # Check for unique usernames across all sections
                    usernames = set()
                    for section in parser.sections():
                        if parser.has_option(section, "username"):
                            username = parser.get(section, "username")
                            if username in usernames:
                                log.critical(f"Duplicate username '{username}' found in {self.cfg.config_file_path}.")
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

            except portalocker.LockTimeout:
                log.critical("Timeout waiting for credentials file lock.")
                self._credentials = None
                assert isinstance(self._credentials, dict)
                return False
            except Exception as e:
                log.critical(f"Unable to load credentials: {str(e)}.")
                self._credentials = None
                assert isinstance(self._credentials, dict)
                return False

    def update_credentials(self, username, password_hash):
        with self._lock:
            try:
                # Use portalocker with write lock
                with portalocker.Lock(self.cfg.config_file_path, 'r+', timeout=10) as cred_file:
                    parser = ConfigParser()
                    parser.read_file(cred_file)

                    # Update or add user
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            parser.set(section, "password", password_hash)
                            found = True
                            break

                    if not found:
                        section_name = f"user_{username}"
                        parser.add_section(section_name)
                        parser.set(section_name, "username", username)
                        parser.set(section_name, "password", password_hash)

                    # Write back to file
                    cred_file.seek(0)
                    cred_file.truncate()
                    parser.write(cred_file)

                    # Reload credentials in memory
                    return self.parse_credentials()

            except portalocker.LockTimeout:
                log.error("Timeout waiting for credentials file lock during update.")
                return False
            except Exception as e:
                log.error(f"Error updating credentials: {str(e)}")
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

    # We try to clean up owned locks on exit to avoid deadlocks on WSGI server exit or interruptions
    def __exit__(self, exc_type, exc_val, exc_tb):
        with suppress(Exception):
            if self._lock._is_owned():
                self._lock.release()
