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
    def __init__(self, config_file_path=None):
        self._lock = threading.RLock()
        self._credentials = None
        self.config_file_path = config_file_path or config.default_config_file_path

    @property
    def credentials(self):
        with self._lock:
            return self._credentials

    @credentials.setter
    def credentials(self, value):
        with self._lock:
            self._credentials = value

    def parse_credentials(self):
        with self._lock:
            try:
                parser = ConfigParser()
                log.info("Loading credentials")
                log.info(self.config_file_path)
                parser.read(self.config_file_path)

                if not parser.has_section("default"):
                    log.critical(f"No [default] credential available for {self.config_file_path}")
                    self._credentials = None
                    assert isinstance(self._credentials, dict)
                    return False

                new_credentials = {}
                for section_name in parser.sections():
                    new_credentials[str(section_name)] = []
                    for name, value in parser.items(section_name):
                        new_credentials[str(section_name)].append({str(name): str(value)})

                self._credentials = new_credentials
                return True

            except Exception as e:
                log.critical(f"Unable to load credentials: {str(e)}")
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
                log.error(f"Error validating credentials: {str(e)}")
                return False

    @property
    def is_loaded(self):
        with self._lock:
            return self._credentials is not None
