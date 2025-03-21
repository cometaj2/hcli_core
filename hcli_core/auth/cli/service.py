import json
import io

from hcli_core import logger
from hcli_core import config

from hcli_core.auth.cli import credential
from hcli_problem_details import *

from functools import wraps

log = logger.Logger("hcli_core")


# Additional authentication check on all service calls just in case authentication is somehow bypassed
def requires_auth(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if not cfg.auth:
            msg = f"cannot interact with hco when authentication is disabled."
            log.warning(msg)
            raise AuthenticationError(detail=msg)
        return func(self, *args, **kwargs)
    return wrapper

# Simple RBAC controls for credentials update.
# A user can update their own password only but the admin can update anything
class Service:
    def __init__(self):
        self.cm = credential.CredentialManager()
        cfg = self._cfg()

    @requires_auth
    def useradd(self, username):
        requesting_username = config.ServerContext.get_current_user()
        return self.cm.useradd(username)

    @requires_auth
    def userdel(self, username):
        requesting_username = config.ServerContext.get_current_user()
        return self.cm.userdel(username)

    @requires_auth
    def passwd(self, username, password_stream):

        if not password_stream:
            msg = "no password provided."
            log.error(msg)
            raise BadRequestError(detail=msg)

        # Read password from stream
        password = password_stream.getvalue().decode().strip()
        if not password:
            msg = "empty password."
            log.error(msg)
            raise BadRequestError(detail=msg)

        requesting_username = config.ServerContext.get_current_user()
        requesting_user_roles = self.cm.get_user_roles(requesting_username)

        # Allow password change if user is changing their own password or has admin role
        if requesting_username != username and 'admin' not in requesting_user_roles:
            msg = f"the password can only be updated for {requesting_username}."
            log.warning(msg)
            raise AuthorizationError(detail=msg)

        return self.cm.passwd(username, password)

    @requires_auth
    def ls(self):
        requesting_username = config.ServerContext.get_current_user()

        users = ""
        if self.cm.credentials:
            for section, creds in self.cm.credentials.items():
                for cred in creds:
                    if "username" in cred:
                        user = cred["username"]
                        users += user + "\n"

        return users.rstrip()

    @requires_auth
    def key(self, username):
        requesting_username = config.ServerContext.get_current_user()
        requesting_user_roles = self.cm.get_user_roles(requesting_username)

        # Allow password change if user is changing their own password or has admin role
        if requesting_username != username and 'admin' not in requesting_user_roles:
            msg = f"cannot create api keys for {username} as {requesting_username}."
            log.warning(msg)
            raise AuthorizationError(detail=msg)

        return self.cm.create_key(username)

    @requires_auth
    def key_rm(self, keyid):
        requesting_username = config.ServerContext.get_current_user()
        return self.cm.delete_key(requesting_username, keyid)

    @requires_auth
    def key_rotate(self, keyid):
        requesting_username = config.ServerContext.get_current_user()
        return self.cm.rotate_key(requesting_username, keyid)

    @requires_auth
    def key_ls(self):
        requesting_username = config.ServerContext.get_current_user()
        return self.cm.list_keys(requesting_username)

    @requires_auth
    def validate_basic(self, username, password_stream):

        if not password_stream:
            msg = "no password provided."
            log.error(msg)
            raise BadRequestError(detail=msg)

        # Read password from stream
        password = password_stream.getvalue().decode().strip()
        if not password:
            msg = "empty password."
            log.error(msg)
            raise BadRequestError(detail=msg)

        requesting_username = config.ServerContext.get_current_user()
        requesting_user_roles = self.cm.get_user_roles(requesting_username)

        if 'admin' not in requesting_user_roles and 'validator' not in requesting_user_roles:
            msg = f"{requesting_username} cannot validate credentials without the validator role."
            log.warning(msg)
            raise AuthorizationError(detail=msg)

        valid = self.cm.validate_basic(username, password)
        result = "invalid"
        if valid is True:
            result = "valid"

        msg = f"{requesting_username} is validating user {username} for HTTP Basic Authentication. {result}."
        if result == "valid":
            log.info(msg)
        else:
            log.warning(msg)

        return result

    @requires_auth
    def validate_hcoak(self, keyid, apikey_stream):

        if not apikey_stream:
            msg = "no apikey provided."
            log.error(msg)
            raise BadRequestError(detail=msg)

        apikey = apikey_stream.getvalue().decode().strip()
        if not apikey:
            msg = "empty apikey."
            log.error(msg)
            raise BadRequestError(detail=msg)

        valid = self.cm.validate_hcoak(keyid, apikey)
        result = "invalid"
        if valid is True:
            result = "valid"

        requesting_username = config.ServerContext.get_current_user()
        requesting_user_roles = self.cm.get_user_roles(requesting_username)

        if 'admin' not in requesting_user_roles and 'validator' not in requesting_user_roles:
            msg = f"{requesting_username} cannot validate credentials without the validator role."
            log.warning(msg)
            raise AuthorizationError(detail=msg)

        msg = f"{requesting_username} is validating keyid {keyid} for HCLI Core API Key Authentication. {result}."
        if result == "valid":
            log.info(msg)
        else:
            log.warning(msg)

        return result

    @requires_auth
    def role_add(self, username, role):
        return self.cm.add_user_role(username, role)

    @requires_auth
    def role_rm(self, username, role):
        return self.cm.remove_user_role(username, role)

    @requires_auth
    def role_ls(self):
        requesting_username = config.ServerContext.get_current_user()

        users = ""
        if self.cm.credentials:
            for section, creds in self.cm.credentials.items():
                for cred in creds:
                    if "username" in cred:
                        user = cred["username"]
                        user_roles = self.cm.get_user_roles(user)
                        users += user + "    " + str(", ".join(user_roles)) + "\n"

        return users.rstrip()

    def _cfg(self):
        context = config.ServerContext.get_current_server()
        return config.Config(context)
