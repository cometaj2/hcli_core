import json
import io
from functools import partial

from hcli_core import logger
from hcli_core.auth.cli import credential
from hcli_core.auth.cli import service as s
from hcli_core import config
from hcli_problem_details import *

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
        log.debug(self.commands)

        if len(self.commands) < 2:
            return None

        command = self.commands[1]

        if command == "useradd":
            username = self.commands[2]
            status = self.service.useradd(username)
            return io.BytesIO((status).encode())

        elif command == "userdel":
            username = self.commands[2]
            status = self.service.userdel(username)
            return io.BytesIO((status).encode())

        elif command == "passwd":
            username = self.commands[2]

            if self.inputstream is None:
                msg = "no password provided."
                log.error(msg)
                raise BadRequestError(detail=msg)

            f = io.BytesIO()
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

            status = self.service.passwd(username, f)
            return io.BytesIO((status).encode())

        elif command == "ls":
            users = self.service.ls()
            return io.BytesIO((users).encode())

        elif command == "key":
            if self.commands[2] == "rm":
                keyid = self.commands[3]
                status = self.service.key_rm(keyid)
                return io.BytesIO((status).encode())
            elif self.commands[2] == "rotate":
                keyid = self.commands[3]
                status = self.service.key_rotate(keyid)
                return io.BytesIO((status).encode())
            elif self.commands[2] == "ls":
                status = self.service.key_ls()
                return io.BytesIO((status).encode())
            else:
                username = self.commands[2]
                status = self.service.key(username)
                return io.BytesIO((status).encode())

        elif command == "validate":
            if self.commands[2] == "basic":
                username = self.commands[3]

                if self.inputstream is None:
                    msg = "no password provided."
                    log.error(msg)
                    raise BadRequestError(detail=msg)

                f = io.BytesIO()
                for chunk in iter(partial(self.inputstream.read, 16384), b''):
                    f.write(chunk)

                status = self.service.validate_basic(username, f)
                return io.BytesIO((status).encode())
            elif self.commands[2] == "hcoak":
                keyid = self.commands[3]

                if self.inputstream is None:
                    msg = "no apikey provided."
                    log.error(msg)
                    raise BadRequestError(detail=msg)

                f = io.BytesIO()
                for chunk in iter(partial(self.inputstream.read, 16384), b''):
                    f.write(chunk)

                status = self.service.validate_hcoak(keyid, f)
                return io.BytesIO((status).encode())

        elif command == "role":
            if self.commands[2] == "add":
                username = self.commands[3]
                role = self.commands[4]
                roleadd = self.service.role_add(username, role)

            elif self.commands[2] == "rm":
                username = self.commands[3]
                role = self.commands[4]
                rolerm = self.service.role_rm(username, role)

            elif self.commands[2] == "ls":
                rolels = self.service.role_ls()
                return io.BytesIO((rolels).encode())

        return None
