import json
import io

from hcli_core import logger

from hcli_core.auth import credential

log = logger.Logger("hcli_core")


class Service:
    def __init__(self):
        self.cm = credential.CredentialManager()

    def useradd(self, username):
        try:
            return self.cm.useradd(username)
        except Exception as e:
            log.error(e)
            return e

    def userdel(self, username):
        try:
            if username == "admin":
                msg = "cannot delete admin user."
                log.warning(msg)
                return msg

            return self.cm.userdel(username)
        except Exception as e:
            msg = f"error deleting user: {username}."
            log.error(msg)
            return msg

    def passwd(self, username, password_stream):
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

            return self.cm.passwd(username, password)

        except Exception as e:
            msg = f"error changing password: {str(e)}."
            log.error(msg)
            return msg

    def ls(self):
        users = []
        if self.cm.credentials:
            for section, creds in self.cm.credentials.items():
                for cred in creds:
                    if "username" in cred:
                        users.append({
                            "username": cred["username"],
                        })
        return users
