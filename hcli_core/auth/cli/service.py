import json
import io

from hcli_core import logger
from hcli_core import config

from hcli_core.auth import credential

from functools import wraps

log = logger.Logger("hco")

# Additional authentication check on all service calls just in case authentication is somehow bypassed
def requires_auth(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if not cfg.auth:
            msg = f"cannot interact with hco when authentication is disabled."
            log.warning(msg)
            return msg
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

        try:
            if requesting_username != "admin":
                msg = f"cannot add user as {requesting_username}."
                log.warning(msg)
                return msg

            return self.cm.useradd(username)
        except Exception as e:
            log.error(e)
            return e

    @requires_auth
    def userdel(self, username):
        requesting_username = config.ServerContext.get_current_user()

        try:
            if requesting_username != "admin":
                msg = f"cannot delete user as {requesting_username}."
                log.warning(msg)
                return msg

            return self.cm.userdel(username)
        except Exception as e:
            msg = f"error deleting user {username}."
            log.error(msg)
            return msg

    @requires_auth
    def passwd(self, username, password_stream):
        requesting_username = config.ServerContext.get_current_user()

        try:
            if not password_stream:
                msg = "no password provided."
                log.error(msg)
                return msg

            # Read password from stream
            password = password_stream.getvalue().decode().strip()
            if not password:
                msg = "empty password."
                log.error(msg)
                return msg

            # The admin can update any user
            if requesting_username != username and not requesting_username == "admin":
                msg = f"the password can only be updated for {requesting_username}."
                log.warning(msg)
                return msg

            return self.cm.passwd(username, password)

        except Exception as e:
            msg = f"error changing password: {str(e)}"
            log.error(msg)
            return msg

    @requires_auth
    def ls(self):
        requesting_username = config.ServerContext.get_current_user()

        if requesting_username != "admin":
            msg = f"cannot list users as {requesting_username}."
            log.warning(msg)
            return msg

        users = ""
        if self.cm.credentials:
            for section, creds in self.cm.credentials.items():
                for cred in creds:
                    if "username" in cred:
                        users += cred["username"] + "\n"

        return users.rstrip()

    @requires_auth
    def key(self, username):
        requesting_username = config.ServerContext.get_current_user()

        try:
            # The admin can update any user
            if requesting_username != username and not requesting_username == "admin":
                msg = f"cannot create api keys for {username} as {requesting_username}."
                log.warning(msg)
                return msg

            return self.cm.create_key(username)

        except Exception as e:
            msg = f"error changing password: {str(e)}"
            log.error(msg)
            return msg

    @requires_auth
    def key_rm(self, keyid):
        requesting_username = config.ServerContext.get_current_user()

        try:
            return self.cm.delete_key(requesting_username, keyid)

        except Exception as e:
            msg = f"error removing api key: {str(e)}"
            log.error(msg)
            return msg

    @requires_auth
    def key_rotate(self, keyid):
        requesting_username = config.ServerContext.get_current_user()

        try:
            return self.cm.rotate_key(requesting_username, keyid)

        except Exception as e:
            msg = f"error rotating api key: {str(e)}"
            log.error(msg)
            return msg

    def _cfg(self):
        context = config.ServerContext.get_current_server()
        return config.Config(context)
