import json
import io

from hcli_core import logger
from hcli_core import config

from hcli_core.auth import credential

log = logger.Logger("hcli_core")


# Simple RBAC controls for credentials update.
# A user can update their own password only but the admin can update anything
class Service:
    def __init__(self):
        self.cm = credential.CredentialManager()

    def useradd(self, username):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if cfg.auth:
            try:
                if requesting_username != "admin":
                    msg = f"cannot add user as {requesting_username}."
                    log.warning(msg)
                    return msg

                return self.cm.useradd(username)
            except Exception as e:
                log.error(e)
                return e
        else:
            msg = f"cannot add user as {requesting_username} when authentication is disabled."
            log.warning(msg)
            return msg

    def userdel(self, username):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if cfg.auth:
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
        else:
            msg = f"cannot delete user as {requesting_username} when authentication is disabled."
            log.warning(msg)
            return msg

    def passwd(self, username, password_stream):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if cfg.auth:
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
        else:
            msg = f"cannot update password as {requesting_username} when authentication is disabled."
            log.warning(msg)
            return msg

    def ls(self):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if cfg.auth:
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
        else:
            msg = f"cannot list users as {requesting_username} when authentication is disabled."
            log.warning(msg)
            return msg


        return users.rstrip()

    def key(self, username):
        requesting_username = config.ServerContext.get_current_user()
        cfg = self._cfg()

        if cfg.auth:
            try:
                # The admin can update any user
                if requesting_username != username and not requesting_username == "admin":
                    msg = f"an api key cannot be created for {username} by {requesting_username}."
                    log.warning(msg)
                    return msg

                return self.cm.key(username)

            except Exception as e:
                msg = f"error changing password: {str(e)}"
                log.error(msg)
                return msg
        else:
            msg = f"cannot update password as {requesting_username} when authentication is disabled."
            log.warning(msg)
            return msg

    def _cfg(self):
        context = config.ServerContext.get_current_server()
        return config.Config(context)
