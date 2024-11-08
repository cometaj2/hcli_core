import sys
import os
import json
import hashlib
import threading
from configparser import ConfigParser
from contextlib import suppress

from hcli_core import logger
from hcli_core import config

log = logger.Logger("hcli_core")

class CredentialManager:
    _instance = None
    _initialized = False
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        # Only initialize once
        if not CredentialManager._initialized:
            with self._lock:
                if not CredentialManager._initialized:
                    self._credentials = None
                    self.cfg = config.Config()
                    self.parse_configuration()
                    CredentialManager._initialized = True

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
                with open(self.cfg.config_file_path, 'r') as config_file:
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
            except Exception as e:
                log.critical(f"Unable to load configuration: {str(e)}")
                assert isinstance(auth, str)

    def parse_credentials(self):
        with self._lock:
            try:
                with open(self.cfg.config_file_path, 'r') as cred_file:
                    parser = ConfigParser()
                    log.info("Loading credentials")
                    log.info(self.cfg.config_file_path)
                    parser.read_file(cred_file)

                    # Check if we have a default section for the admin user
                    if not parser.has_section("default"):
                        msg = f"No [default] credential available for {self.cfg.config_file_path}."
                        log.critical(msg)
                        self._credentials = None
                        #assert isinstance(self._credentials, dict)
                        return msg

                    # Check if we have a default admin username and password
                    if not parser.has_option("default", "username") or parser.get("default", "username") != "admin" or not parser.has_option("default", "password"):
                        msg = f"Invalid or missing admin username or password in [default] section of {self.cfg.config_file_path}."
                        log.critical(msg)
                        self._credentials = None
                        #assert isinstance(self._credentials, dict)
                        return msg

                    # Check for unique usernames across all sections
                    usernames = set()
                    for section in parser.sections():
                        if parser.has_option(section, "username"):
                            username = parser.get(section, "username")
                            if username in usernames:
                                msg = f"duplicate username '{username}' found in {self.cfg.config_file_path}."
                                log.critical(msg)
                                self._credentials = None
                                #assert isinstance(self._credentials, dict)
                                return msg
                            usernames.add(username)

                    new_credentials = {}
                    for section_name in parser.sections():
                        new_credentials[str(section_name)] = []
                        for name, value in parser.items(section_name):
                            new_credentials[str(section_name)].append({str(name): str(value)})

                    self._credentials = new_credentials
                    return

            except Exception as e:
                msg = f"unable to load credentials: {str(e)}."
                log.critical(msg)
                self._credentials = None
                #assert isinstance(self._credentials, dict)
                return msg

    def useradd(self, username):
        with self._lock:
            try:
                with open(self.cfg.config_file_path, 'r') as cred_file:
                    parser = ConfigParser()
                    parser.read_file(cred_file)

                    # Update or add user
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            found = True
                            msg = f"user {username} already exists."
                            log.warning(msg)
                            return msg

                    if not found:
                        section_name = f"user_{username}"
                        parser.add_section(section_name)
                        parser.set(section_name, "username", username)
                        parser.set(section_name, "password", "*")

                # Write back to file
                with open(self.cfg.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self.parse_credentials()
                msg = f"user {username} added."
                log.info(msg)
                return msg

            except Exception as e:
                msg = f"error updating credentials: {str(e)}."
                log.error(msg)
                return msg

    def passwd(self, username, password):
        with self._lock:
            try:
                with open(self.cfg.config_file_path, 'r') as cred_file:
                    parser = ConfigParser()
                    parser.read_file(cred_file)

                    # Update or add user
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            password_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()
                            parser.set(section, "password", password_hash)
                            found = True
                            break

                    if not found:
                        msg = f"user {username} not found."
                        log.warning(msg)
                        return msg

                # Write back to file
                with open(self.cfg.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self.parse_credentials()
                msg = f"credentials updated for user {username}."
                log.info(msg)
                return msg

            except Exception as e:
                msg = f"error updating credentials: {str(e)}."
                log.error(msg)
                return msg

    def userdel(self, username):
        with self._lock:
            try:
                # Read current configuration
                with open(self.cfg.config_file_path, 'r') as cred_file:
                    parser = ConfigParser()
                    parser.read_file(cred_file)

                    # Find and remove user section
                    user_section = None
                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            user_section = section
                            break

                    if user_section is None:
                        msg = f"user {username} not found."
                        log.warning(msg)
                        return msg

                    # Remove the section
                    parser.remove_section(user_section)

                # Write back to file
                with open(self.cfg.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self.parse_credentials()
                msg = f"user {username} deleted."
                log.info(msg)
                return msg

            except Exception as e:
                msg = f"error deleting {username}: {str(e)}"
                log.error(msg)
                return msg

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
                msg = f"error validating credentials: {str(e)}."
                log.error(msg)
                return False

    @property
    def is_loaded(self):
        with self._lock:
            return self._credentials is not None

    def __exit__(self, exc_type, exc_val, exc_tb):
        with suppress(Exception):
            if self._lock._is_owned():
                self._lock.release()
