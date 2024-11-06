import json
import io
from functools import partial

from hcli_core import logger
from hcli_core.auth import credential
from hcli_core.auth.cli import service as s

log = logger.Logger("hcli_core")


class CLI:
    commands = None
    inputstream = None
    service = None

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.service = s.Service()

    def execute(self):
        if len(self.commands) < 2:
            return None

        command = self.commands[1]

        # Handle useradd command
        if command == "useradd":
            if len(self.commands) < 3:
                log.error("Username required")
                return None
            username = self.commands[2]
            if self.service.useradd(username):
                return io.BytesIO(f"User account created: {username}.\n".encode())
            return io.BytesIO("Failed to create user.\n".encode())

        # Handle userdel command
        elif command == "userdel":
            if len(self.commands) < 3:
                log.error("Username required")
                return None
            username = self.commands[2]
            if self.service.userdel(username):
                return io.BytesIO(f"User account deleted: {username}.\n".encode())
            return io.BytesIO("Failed to delete user.\n".encode())

        # Handle passwd command
        elif command == "passwd":
            if len(self.commands) < 3:
                log.error("Username required")
                return None
            username = self.commands[2]

            if self.inputstream is None:
                log.error("No password provided")
                return None

            f = io.BytesIO()
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

            if self.service.passwd(username, f):
                return io.BytesIO(f"Password updated for user: {username}.\n".encode())
            return io.BytesIO("Failed to update password.\n".encode())

        # Handle list command (optional, not in template but useful)
        elif command == "list":
            users = self.service.list_users()
            return io.BytesIO(json.dumps(users, indent=4).encode("utf-8"))

        return None
