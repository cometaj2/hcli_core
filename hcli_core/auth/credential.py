import sys
import os
import json
import hashlib
import base64
import threading
import time
from datetime import datetime, timezone, timedelta
from configparser import ConfigParser
from contextlib import suppress

from hcli_core import logger
from hcli_core import config

log = logger.Logger("hcli_core")


class CredentialManager:
    _instance = None
    _initialized = False
    _lock = threading.RLock()

    def __new__(cls, config_file_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__init__(config_file_path)
            return cls._instance

    # The config here is biased but so happens to be the same for config_file_path for both core and management
    # This is not a good implementation and should be fixed.
    # Only initialize once
    def __init__(self, config_file_path=None):
        if not CredentialManager._initialized:
            with self._lock:
                if not CredentialManager._initialized:
                    self._credentials = None
                    self.config_file_path = config_file_path
                    self._bootstrap_password = None
                    self._parse_credentials()
                    CredentialManager._initialized = True

    @property
    def credentials(self):
        with self._lock:
            return self._credentials

    @credentials.setter
    def credentials(self, value):
        with self._lock:
            self._credentials = value

    def _parse_credentials(self):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    log.info("Loading credentials")
                    log.info(self.config_file_path)
                    parser.read_file(cred_file)

                    # Check if we have a default section for the admin user
                    if not parser.has_section("default"):
                        msg = f"No [default] credential available for {self.config_file_path}."
                        log.warning(msg)
                        self._credentials = None
                        return msg

                    # Check if we have a default admin username and password
                    if not parser.has_option("default", "username") or parser.get("default", "username") != "admin" or not parser.has_option("default", "password"):
                        msg = f"Invalid or missing admin username or password in [default] section of {self.config_file_path}."
                        log.warning(msg)
                        self._credentials = None
                        return msg

                    # Check if we have a salt
                    if not parser.has_option("default", "salt"):
                        msg = f"Invalid or missing salt in [default] section of {self.config_file_path}."
                        log.warning(msg)
                        self._credentials = None
                        return msg

                    # Check for unique usernames across all sections
                    usernames = set()
                    for section in parser.sections():
                        if parser.has_option(section, "username"):
                            username = parser.get(section, "username")
                            if username in usernames:
                                msg = f"duplicate username '{username}' found in {self.config_file_path}."
                                log.critical(msg)
                                self._credentials = None
                                return msg
                            usernames.add(username)

                    new_credentials = {}
                    for section_name in parser.sections():
                        new_credentials[str(section_name)] = []
                        for name, value in parser.items(section_name):
                            new_credentials[str(section_name)].append({str(name): str(value)})

                    self._credentials = new_credentials

                    if self.is_admin_reset_state():
                        self.bootstrap()

                    return

            except Exception as e:
                msg = f"unable to load credentials: {str(e)}."
                log.error(msg)
                self._credentials = None
                #assert isinstance(self._credentials, dict)
                return msg

    def useradd(self, username):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
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
                        parser.set(section_name, "salt", "*")

                # Write back to file
                with open(self.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self._parse_credentials()
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
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Update or add user
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            (password_hash, salt) = self.hash_password(password)
                            parser.set(section, "salt", salt)
                            parser.set(section, "password", password_hash)

                            # We reset the special admin bootstrap case
                            if username == 'admin' and self._bootstrap_password is not None:
                                self._bootstrap_password = None

                            found = True
                            break

                    if not found:
                        msg = f"user {username} not found."
                        log.warning(msg)
                        return msg

                # Write back to file
                with open(self.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self._parse_credentials()
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
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
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
                with open(self.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self._parse_credentials()
                msg = f"user {username} deleted."
                log.info(msg)
                return msg

            except Exception as e:
                msg = f"error deleting {username}: {str(e)}"
                log.error(msg)
                return msg

    def validate(self, username, password):
        with self._lock:
            # Special case for bootstrap password
            if self._bootstrap_password is not None:
                if username == 'admin':
                    bootstrap_valid = password == self._bootstrap_password
                    return bootstrap_valid
            else:
                try:
                    if not self._credentials:
                        return False

                    # Find the right section by username
                    for section, cred_list in self._credentials.items():
                        cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

                        if cred_dict.get('username') == username:
                            stored_hash = cred_dict.get('password')
                            stored_salt = cred_dict.get('salt')

                            if stored_hash and stored_salt and not stored_hash == '*' and not stored_salt == '*':
                                return self.verify_password(password, stored_hash, stored_salt)
                            break  # Found username but or missing hash/salt or bootstrap hash/salt

                    return False

                except Exception as e:
                    msg = f"error validating credentials: {str(e)}."
                    log.error(msg)
                    return False

    def validate_hcoak(self, apikey):
        with self._lock:
            try:
                if not self._credentials:
                    return False

                # Find the right section by username
                for section, cred_list in self._credentials.items():
                    cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

                    if cred_dict.get('apikey') == apikey:
                        return True

                return False

            except Exception as e:
                msg = f"error validating credentials: {str(e)}."
                log.error(msg)
                return False

    # Hash password using 600000 (1Password/LastPass) iterations of PBKDF2-SHA256 with 32 bit salt.
    # dklen of 32 for sha256, 64 for sha512
    def hash_password(self, password):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations=600000, dklen=32)
        return key.hex(), salt.hex()

    # Verify password against stored hash and salt (both in hex format).
    # dklen of 32 for sha256, 64 for sha512
    def verify_password(self, password, stored_hash, salt_hex):
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations=600000, dklen=32)
        return key.hex() == stored_hash

    # Generate one-time setup password for the administrator that needs to be changed immediately
    def generate_bootstrap_password(self):
        raw_password = os.urandom(32)
        password = base64.b64encode(os.urandom(32)).decode('utf-8')
        return password

    @property
    def is_loaded(self):
        with self._lock:
            return self._credentials is not None

    def is_admin_reset_state(self):
        reset_state = False

        # Find the right section by username
        for section, cred_list in self._credentials.items():
            cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

            if cred_dict.get('username') == 'admin':
                stored_hash = cred_dict.get('password')
                stored_salt = cred_dict.get('salt')

                if stored_hash and stored_salt:
                    reset_state = (stored_hash == '*' and stored_salt == '*')
                    return reset_state
                break

        return reset_state

    def bootstrap(self):
        # Find the right section by username
        for section, cred_list in self._credentials.items():
            cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

            if cred_dict.get('username') == 'admin':
                stored_hash = cred_dict.get('password')
                stored_salt = cred_dict.get('salt')

                if stored_hash and stored_salt:
                    reset_state = (stored_hash == '*' and stored_salt == '*')
                    if reset_state:
                        self._bootstrap_password = self.generate_bootstrap_password()
                        log.critical("================================================")
                        log.critical("HCLI INITIAL ADMIN PASSWORD (CHANGE IMMEDIATELY)")
                        log.critical("Username: admin")
                        log.critical(f"Password: {self._bootstrap_password}")
                        log.critical("This password will only be shown once in logs")
                        log.critical("================================================")
                        self.passwd('admin', self._bootstrap_password)
                        self._bootstrap_password = None
                        return
                break
        return

    def key(self, username):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    found = False
                    highest_key_num = 0
                    base_section = f"{username}_apikey"

                    for section in parser.sections():
                        if parser.has_option(section, "username") and parser.get(section, "username") == username:
                            found = True
                        # Look for existing apikey sections and find highest number
                        if section.startswith(base_section):
                            try:
                                key_num = int(section[len(base_section):] or 0)
                                highest_key_num = max(highest_key_num, key_num)
                            except ValueError:
                                continue

                    if not found:
                        msg = f"user {username} doesn't exist."
                        log.warning(msg)
                        return msg

                    # Create new section with next number
                    section_name = f"{username}_apikey{highest_key_num + 1}"
                    parser.add_section(section_name)
                    (apikey, created) = self.generate_apikey()
                    keyid = self.generate_keyid()
                    parser.set(section_name, "keyid", keyid)
                    parser.set(section_name, "parent", username)
                    parser.set(section_name, "apikey", str(apikey))
                    parser.set(section_name, "created", str(created))
                    parser.set(section_name, "status", "valid")

                # Write back to file
                with open(self.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)

                # Reload credentials in memory
                self._parse_credentials()
                msg = f"api key {keyid} created for user {username}."
                log.info(msg)
                return keyid + "    " + apikey + "    " + created

            except Exception as e:
                msg = f"error updating credentials: {str(e)}."
                log.error(msg)
                return msg

    # Or base32 approach (10 chars) to help avoid 1/I 0/O visual discrepancies.
    def generate_keyid(self):
        random_bytes = os.urandom(6)  # 6 bytes = 10 chars in base32
        keyid = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
        return keyid

    # Generate a secure random api key. Example: hco_apikey_gCUipvHmFDPw82x-MZ9djsOPGq_kxD4gks...
    # hcoak for hco hcli api key
    def generate_apikey(self, prefix='hcoak'):
        random_bytes = os.urandom(64)
        key_part = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
        key = f"{prefix}_{key_part}"

        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        dt = datetime.now().replace(tzinfo=timezone(timedelta(seconds=-offset)))
        formatted = dt.isoformat()

        return key, formatted

    def __exit__(self, exc_type, exc_val, exc_tb):
        with suppress(Exception):
            if self._lock._is_owned():
                self._lock.release()
