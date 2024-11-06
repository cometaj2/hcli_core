import json
import io
import hashlib

from hcli_core import logger

from hcli_core.auth import credential

log = logger.Logger("hcli_core")


class Service:
    def __init__(self):
        self.cm = credential.CredentialManager()

    def useradd(self, username):
        try:
            if self.cm.useradd(username):
                log.info(f"Created user account: {username}")
                return True
            return False
        except Exception as e:
            log.error(e)
            return False

    def userdel(self, username):
        try:
            if username == "admin":
                log.warning("Cannot delete admin user")
                return False

            if self.cm.userdel(username):
                log.info(f"Deleted user account: {username}")
                return True
            return False
        except Exception as e:
            log.error(e)
            return False

        except Exception as e:
            log.error(f"Error deleting user: {str(e)}")
            return False

    def passwd(self, username, password_stream):
        try:
            if not password_stream:
                log.error("No password provided")
                return False

            # Read password from stream
            password = password_stream.getvalue().decode().strip()
            if not password:
                log.error("Empty password")
                return False

            # Hash and update
            password_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()
            if self.cm.passwd(username, password_hash):
                log.info(f"Updated password for user: {username}")
                return True

            return False

        except Exception as e:
            log.error(f"Error changing password: {str(e)}")
            return False

    def ls(self):
        """List all users"""
        users = []
        if self.cm.credentials:
            for section, creds in self.cm.credentials.items():
                for cred in creds:
                    if "username" in cred:
                        users.append({
                            "username": cred["username"],
                            "section": section
                        })
        return users
