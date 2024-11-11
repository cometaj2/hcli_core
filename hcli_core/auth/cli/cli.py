import json
import io
from functools import partial

from hcli_core import logger
from hcli_core.auth import credential
from hcli_core.auth.cli import service as s
from hcli_core import config

log = logger.Logger("hco")


class CLI:
    commands = None
    inputstream = None
    service = None

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.service = s.Service()

    def execute(self):
        log.info(self.commands)

        if len(self.commands) < 2:
            return None

        command = self.commands[1]

        if command == "useradd":
            username = self.commands[2]
            status = self.service.useradd(username)
            return io.BytesIO((status+"\n").encode())

        elif command == "userdel":
            username = self.commands[2]
            status = self.service.userdel(username)
            return io.BytesIO((status+"\n").encode())

        elif command == "passwd":
            username = self.commands[2]

            if self.inputstream is None:
                msg = "no password provided."
                log.error(msg)
                return io.BytesIO((msg+"\n").encode())

            f = io.BytesIO()
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

            status = self.service.passwd(username, f)
            return io.BytesIO((status+"\n").encode())

        elif command == "ls":
            users = self.service.ls()
            return io.BytesIO((users+"\n").encode())

        elif command == "key":
            username = self.commands[2]
            status = self.service.key(username)
            return io.BytesIO((status+"\n").encode())

        return None
