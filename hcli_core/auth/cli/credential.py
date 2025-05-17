import os
import inspect
import io
import hashlib
import base64
import threading
import time
import portalocker

from datetime import datetime, timezone, timedelta
from configparser import ConfigParser
from contextlib import suppress, contextmanager
from pathlib import Path
from huckle import stdin, cli

from hcli_core import logger
from hcli_core import config
from hcli_problem_details import *

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

                    if not config_file_path:
                        self.config_file_path = os.path.join(os.path.dirname(inspect.getfile(lambda: None)), "credentials")
                    else:
                        self.config_file_path = config_file_path

                    self._last_refresh = 0
                    self._credentials_ttl = 5  # Eventually consistent every 5 seconds

                    # This helps guarantee multiprocess handling on the bootstrap case
                    # (only 1 process sets the bootstrap password and the rest follow suit)
                    with self._write_lock():
                        self._parse_credentials()
                        if self._is_admin_reset_state():
                            self._bootstrap()

                    self._bootstrap_password = None
                    CredentialManager._initialized = True

    @property
    def credentials(self):
        with self._lock:
            return self._credentials

    @credentials.setter
    def credentials(self, value):
        with self._lock:
            self._credentials = value

    @contextmanager 
    def _write_lock(self):
        lockfile = Path(self.config_file_path).with_suffix('.lock')
        with portalocker.Lock(lockfile, timeout=10) as lock:
            yield

    # Get credentials with TTL-based refresh
    def _get_credentials(self):
        with self._lock:
            with self._write_lock():
                current_time = time.time()
                if current_time - self._last_refresh > self._credentials_ttl:
                    self._parse_credentials()
                return self._credentials

    def _parse_credentials(self):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    log.debug("Loading credentials:")
                    log.debug(self.config_file_path)
                    parser.read_file(cred_file)

                    # Check if we have a default section for the admin user
                    if not parser.has_section("default"):
                        msg1 = f"No [default] admin credential available:"
                        msg2 = f"{self.config_file_path}"
                        log.info(msg1)
                        log.info(msg2)
                        self._credentials = None

                    # Check if we have a default admin username and password
                    elif not parser.has_option("default", "username") or parser.get("default", "username") != "admin" or not parser.has_option("default", "password"):
                        msg1 = f"Invalid or missing admin username or password in [default] section:"
                        msg2 = f"{self.config_file_path}"
                        log.warning(msg1)
                        log.warning(msg2)
                        self._credentials = None

                    # Check if we have a salt
                    elif not parser.has_option("default", "salt"):
                        msg1 = f"Invalid or missing salt in [default] section:"
                        msg2 = f"{self.config_file_path}"
                        log.warning(msg1)
                        log.warning(msg2)
                        self._credentials = None

                    # Check for unique usernames across all sections
                    usernames = set()
                    for section in parser.sections():
                        if parser.has_option(section, "username"):
                            username = parser.get(section, "username")
                            if username in usernames:
                                msg = f"Duplicate username '{username}' found in {self.config_file_path}."
                                log.critical(msg)
                                self._credentials = None
                            usernames.add(username)

                    new_credentials = {}
                    for section_name in parser.sections():
                        new_credentials[str(section_name)] = []
                        for name, value in parser.items(section_name):
                            new_credentials[str(section_name)].append({str(name): str(value)})

                    self._credentials = new_credentials

                    return

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"unable to load credentials: {str(e)}"
                log.error(msg)
                self._credentials = None
                raise InternalServerError(detail=msg)

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
                            raise ConflictError(detail=msg)

                    if not found:
                        section_name = f"user_{username}"
                        parser.add_section(section_name)
                        parser.set(section_name, "username", username)
                        parser.set(section_name, "password", "*")
                        parser.set(section_name, "salt", "*")

                # Write back to file
                with self._write_lock():
                    with open(self.config_file_path, 'w') as cred_file:
                        parser.write(cred_file)
                        cred_file.flush()
                        os.fsync(cred_file.fileno())
                    self._parse_credentials()

                msg = f"user {username} added."
                log.info(msg)
                return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def passwd(self, username, password):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Update
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
                        raise NotFoundError(detail=msg)

                # Write back to file
                with self._write_lock():
                    with open(self.config_file_path, 'w') as cred_file:
                        parser.write(cred_file)
                        cred_file.flush()
                        os.fsync(cred_file.fileno())
                    self._parse_credentials()

                msg = f"credentials updated for user {username}."
                log.info(msg)
                return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    # Special bootstrap case to avoid initial multiprocess deadlock
    def _bootstrap_passwd(self, username, password):
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
                        raise NotFoundError(detail=msg)

                with open(self.config_file_path, 'w') as cred_file:
                    parser.write(cred_file)
                    cred_file.flush()
                    os.fsync(cred_file.fileno())
                self._parse_credentials()

                msg = f"credentials updated for user {username}."
                log.info(msg)
                return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

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
                        raise NotFoundError(detail=msg)

                    # Remove the section
                    parser.remove_section(user_section)

                # Write back to file
                with self._write_lock():
                    with open(self.config_file_path, 'w') as cred_file:
                        parser.write(cred_file)
                        cred_file.flush()
                        os.fsync(cred_file.fileno())
                    self._parse_credentials()

                msg = f"user {username} deleted."
                log.info(msg)
                return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error deleting {username}: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def validate_basic(self, username, password):
        with self._lock:
            try:
                cfg = config.Config(config.ServerContext.get_current_server())
                if cfg.mgmt_credentials == 'remote':
                    chunks = cli("huckle cli config hco url")

                    data = ""
                    stream = ""
                    try:
                        for dest, chunk in chunks:
                            stream = dest
                            data = ''.join(chunk.decode('utf-8'))
                    except Exception as e:
                        log.error(e)
                        return False

                    data = data.rstrip()
                    if stream == 'stderr':
                        log.error(data)
                        return False

                    remote_password = io.BytesIO(password.encode())
                    with stdin(remote_password):
                        log.info(f"Forwarding authentication for {username} to {data}")
                        chunks = cli(f"hco validate basic {username}")

                        data = ""
                        stream = ""
                        try:
                            for dest, chunk in chunks:
                                stream = dest
                                data = ''.join(chunk.decode('utf-8'))
                        except Exception as e:
                            log.error(e)
                            return False

                        data = data.rstrip()
                        if stream == 'stderr':
                            log.error(data)

                        if data == 'valid':
                            return True
                        else:
                            return False

                # Special case for bootstrap password
                if self._bootstrap_password is not None:
                    if username == 'admin':
                        bootstrap_valid = password == self._bootstrap_password
                        return bootstrap_valid
                else:
                    self._get_credentials()
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

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error validating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def validate_hcoak(self, keyid, apikey):
        with self._lock:
            try:
                cfg = config.Config(config.ServerContext.get_current_server())
                if cfg.mgmt_credentials == 'remote':
                    chunks = cli("huckle cli config hco url")

                    data = ""
                    stream = ""
                    try:
                        for dest, chunk in chunks:
                            stream = dest
                            data = ''.join(chunk.decode('utf-8'))
                    except Exception as e:
                        log.error(e)
                        return False

                    data = data.rstrip()
                    if stream == 'stderr':
                        log.error(data)
                        return False

                    remote_apikey = io.BytesIO(apikey.encode())
                    with stdin(remote_apikey):
                        log.info(f"Forwarding authentication for {keyid} to {data}")
                        chunks = cli(f"hco validate hcoak {keyid}")

                        data = ""
                        stream = ""
                        try:
                            for dest, chunk in chunks:
                                if dest == 'stdout':
                                    stream = dest
                                    data = ''.join(chunk.decode('utf-8'))
                                else:
                                    stream = dest
                                    data = ''.join(chunk.decode('utf-8'))
                        except Exception as e:
                            log.error(e)
                            return False

                        data = data.rstrip()
                        if stream == 'stderr':
                            log.error(data)

                        if data == 'valid':
                            return True
                        else:
                            return False

                self._get_credentials()
                if not self._credentials:
                    return False

                # Find the right section by username
                for section, cred_list in self._credentials.items():
                    cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

                    if (cred_dict.get('keyid') == keyid and
                        cred_dict.get('status') == 'valid'):
                        stored_hash = cred_dict.get('apikey')
                        if stored_hash:
                            return self.hash_apikey(apikey) == stored_hash

                return False

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error validating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    # Hash password using 600000 (1Password/LastPass) iterations of PBKDF2-SHA256 with 32 bit salt.
    # dklen of 32 for sha256, 64 for sha512
    def hash_password(self, password):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations=600000, dklen=32)
        return key.hex(), salt.hex()

    def hash_apikey(self, apikey):
        return hashlib.sha256(apikey.encode()).hexdigest()

    # Verify password against stored hash and salt (both in hex format).
    # dklen of 32 for sha256, 64 for sha512
    def verify_password(self, password, stored_hash, salt_hex):
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations=600000, dklen=32)
        return key.hex() == stored_hash

    @property
    def is_loaded(self):
        with self._lock:
            return self._credentials is not None

    def _is_admin_reset_state(self):
        reset_state = False

        if not self._credentials:
            return reset_state

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

    def _bootstrap(self):
        # Find the right section by username
        for section, cred_list in self._credentials.items():
            cred_dict = {k: v for cred in cred_list for k, v in cred.items()}

            if cred_dict.get('username') == 'admin':
                stored_hash = cred_dict.get('password')
                stored_salt = cred_dict.get('salt')

                if stored_hash and stored_salt:
                    reset_state = (stored_hash == '*' and stored_salt == '*')
                    if reset_state:
                        self._bootstrap_password = os.getenv('HCLI_CORE_BOOTSTRAP_PASSWORD')
                        log.warning("===============================================================")
                        log.warning("HCLI BOOTSTRAP PASSWORD (CHANGE IMMEDIATELY AND STORE SECURELY)")
                        log.warning("Username: admin")
                        log.warning("Password: $HCLI_CORE_BOOTSTRAP_PASSWORD environment variable")
                        log.warning("Read 'hcli_core help' documentation for more details")
                        log.warning("This will only be shown in the logs once")
                        log.warning("===============================================================")
                        if not self._bootstrap_password:
                            msg="Missing HCLI_CORE_BOOTSTRAP_PASSWORD environment variable. Unable to bootstrap administration."
                            log.error(msg)
                            return
                        self._bootstrap_passwd('admin', self._bootstrap_password)
                        self._bootstrap_password = None
                        return
                break
        return

    def create_key(self, username):
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
                        raise NotFoundError(detail=msg)

                    # Create new section with next number
                    section_name = f"{username}_apikey{highest_key_num + 1}"
                    parser.add_section(section_name)

                    (apikey, created) = self.generate_apikey()
                    hashed_apikey = self.hash_apikey(apikey)
                    keyid = self.generate_keyid()

                    parser.set(section_name, "keyid", keyid)
                    parser.set(section_name, "owner", username)
                    parser.set(section_name, "apikey", str(hashed_apikey))
                    parser.set(section_name, "created", str(created))
                    parser.set(section_name, "status", "valid")

                # Write back to file
                with self._write_lock():
                    with open(self.config_file_path, 'w') as cred_file:
                        parser.write(cred_file)
                        cred_file.flush()
                        os.fsync(cred_file.fileno())
                    self._parse_credentials()

                msg = f"api key {keyid} created for user {username}."
                log.info(msg)
                return keyid + "    " + apikey + "    " + created

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def delete_key(self, username, keyid):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Find the section with matching keyid
                    target_section = None
                    owner = None
                    for section in parser.sections():
                        if parser.has_option(section, "keyid") and parser.get(section, "keyid") == keyid:
                            owner = parser.get(section, "owner")
                            target_section = section
                            break

                    if target_section is None:
                        msg = f"api key {keyid} not found."
                        log.warning(msg)
                        raise NotFoundError(detail=msg)

                    # Check permissions - allow if user is owner or is admin
                    requesting_user_roles = self.get_user_roles(username)
                    is_admin = 'admin' in requesting_user_roles
                    if not is_admin and owner != username:
                        msg = f"user {username} not authorized to delete key {keyid} owned by {owner}."
                        log.warning(msg)
                        raise AuthorizationError(detail=msg)

                    # Remove the section
                    parser.remove_section(target_section)

                    # Write back to file
                    with self._write_lock():
                        with open(self.config_file_path, 'w') as cred_file:
                            parser.write(cred_file)
                            cred_file.flush()
                            os.fsync(cred_file.fileno())
                        self._parse_credentials()

                    msg = f"api key {keyid} deleted successfully for owner {owner}."
                    log.info(msg)
                    return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error deleting api key: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def rotate_key(self, username, keyid):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Find the section with matching keyid
                    target_section = None
                    owner = None
                    for section in parser.sections():
                        if parser.has_option(section, "keyid") and parser.get(section, "keyid") == keyid:
                            owner = parser.get(section, "owner")
                            target_section = section
                            break

                    if target_section is None:
                        msg = f"api key {keyid} not found."
                        log.warning(msg)
                        raise NotFoundError(detail=msg)

                    # Check permissions - allow if user is owner or is admin
                    requesting_user_roles = self.get_user_roles(username)
                    is_admin = 'admin' in requesting_user_roles
                    if not is_admin and owner != username:
                        msg = f"user {username} cannot rotate key {keyid} owned by {owner}."
                        log.warning(msg)
                        raise AuthorizationError(detail=msg)

                    (apikey, created) = self.generate_apikey()
                    hashed_apikey = self.hash_apikey(apikey)

                    parser.set(target_section, "apikey", str(hashed_apikey))
                    parser.set(target_section, "created", str(created))

                    # Write back to file
                    with self._write_lock():
                        with open(self.config_file_path, 'w') as cred_file:
                            parser.write(cred_file)
                            cred_file.flush()
                            os.fsync(cred_file.fileno())
                        self._parse_credentials()

                    msg = f"api key {keyid} rotated by {username} for {owner}."
                    log.info(msg)
                    return keyid + "    " + apikey + "    " + created

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error deleting api key: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def list_keys(self, username):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Store results
                    key_info = []

                    # Iterate through sections to find API keys
                    for section in parser.sections():
                        if not parser.has_option(section, "keyid"):
                            continue

                        owner = parser.get(section, "owner")

                        # Only show keys if user is admin or owns the key
                        requesting_user_roles = self.get_user_roles(username)
                        is_admin = 'admin' in requesting_user_roles
                        if not is_admin and owner != username:
                            continue

                        keyid = parser.get(section, "keyid")
                        created = parser.get(section, "created")
                        status = parser.get(section, "status")

                        key_info.append(f"{keyid}    {created}    {owner}    {status}")

                    if not key_info:
                        return ""

                    return "\n".join(key_info)

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error listing api keys: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    # Or base32 approach (10 chars) to help avoid 1/I 0/O visual discrepancies.
    def generate_keyid(self):
        random_bytes = os.urandom(6)  # 6 bytes = 10 chars in base32
        keyid = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
        return keyid

    # Generate a secure random api key. Example: hcoak_gCUipvHmFDPw82x-MZ9djsOPGq_kxD4gks...
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

    # Get roles for a user from the credentials file. Returns list of roles.
    def get_user_roles(self, username):
        with self._lock:
            try:
                self._get_credentials()  # Ensure credentials are up to date
                if not self._credentials:
                    return []

                roles = []
                for section, cred_list in self._credentials.items():
                    cred_dict = {k: v for cred in cred_list for k, v in cred.items()}
                    if cred_dict.get('username') == username:
                        # Get roles string from config and split by comma
                        if 'roles' in cred_dict:
                            # Split by comma and strip whitespace from each role
                            roles.extend([role.strip() for role in cred_dict['roles'].split(',')])
                        else:
                            # If no roles specified, add default 'user' role
                            if not username == 'admin':
                                roles.append('user')
                        break

                # Special case for admin user
                if username == 'admin' and 'admin' not in roles:
                    roles.append('admin')

                return roles

            except Exception as e:
                msg = f"error getting roles: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def add_user_role(self, username, role):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Find and update the user's credentials
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, 'username') and parser.get(section, 'username') == username:
                            # Get current roles string
                            current_roles_str = parser.get(section, 'roles', fallback='')

                            # Convert to list and clean whitespace
                            current_roles = [r.strip() for r in current_roles_str.split(',')] if current_roles_str else []

                            # Add role if not present
                            if role not in current_roles:
                                current_roles.append(role)

                            # Handle special cases
                            if username == 'admin' and 'admin' not in current_roles:
                                current_roles.append('admin')
                            elif username != 'admin' and 'user' not in current_roles:
                                current_roles.append('user')

                            # Filter out empty strings and join
                            roles = ','.join([r for r in current_roles if r])

                            # Update config
                            parser.set(section, 'roles', roles)
                            found = True
                            break

                    if not found:
                        msg = f"user {username} not found."
                        log.warning(msg)
                        raise NotFoundError(detail=msg)

                    # Write back to file
                    with self._write_lock():
                        with open(self.config_file_path, 'w') as cred_file:
                            parser.write(cred_file)
                            cred_file.flush()
                            os.fsync(cred_file.fileno())
                        self._parse_credentials()

                    msg = f"roles updated for user {username}."
                    log.info(msg)
                    return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)

    def remove_user_role(self, username, role):
        with self._lock:
            try:
                with open(self.config_file_path, 'r') as cred_file:
                    parser = ConfigParser(interpolation=None)
                    parser.read_file(cred_file)

                    # Find and update the user's credentials
                    found = False
                    for section in parser.sections():
                        if parser.has_option(section, 'username') and parser.get(section, 'username') == username:
                            # Get current roles string
                            current_roles_str = parser.get(section, 'roles', fallback='')

                            # Convert to list and clean whitespace
                            current_roles = [r.strip() for r in current_roles_str.split(',')] if current_roles_str else []

                            # Remove role if present
                            if role in current_roles:
                                current_roles.remove(role)

                            # Handle special cases
                            if username == 'admin':
                                if 'admin' not in current_roles:
                                    current_roles.append('admin')
                            elif 'user' not in current_roles:
                                current_roles.append('user')

                            # Filter out empty strings and join
                            roles = ','.join([r for r in current_roles if r])

                            # Update config
                            parser.set(section, 'roles', roles)
                            found = True
                            break

                    if not found:
                        msg = f"user {username} not found."
                        log.warning(msg)
                        raise NotFoundError(detail=msg)

                    # Write back to file
                    with self._write_lock():
                        with open(self.config_file_path, 'w') as cred_file:
                            parser.write(cred_file)
                            cred_file.flush()
                            os.fsync(cred_file.fileno())
                        self._parse_credentials()

                    msg = f"roles updated for user {username}."
                    log.info(msg)
                    return ""

            except ProblemDetail:
                raise
            except Exception as e:
                msg = f"error updating credentials: {str(e)}"
                log.error(msg)
                raise InternalServerError(detail=msg)
