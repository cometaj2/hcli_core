import json
import io
import channels

import os.path
from os import path
import chroot as ch
from functools import partial
import subprocess

class CLI:
    commands = None
    inputstream = None
    chroot = None
    
    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.chroot = ch.Chroot()

    def execute(self):
        print(self.commands)

        if self.commands[1] == "channel":
            if self.commands[2] == "create":
                if len(self.commands) > 3:
                    n = channels.Channels()
                    s = n.createLogicalChannel(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "mv":
                if len(self.commands) > 3:
                    n = channels.Channels()
                    s = n.renameLogicalChannel(self.commands[3], self.commands[4])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "rm":
                if len(self.commands) > 3:
                    n = channels.Channels()
                    s = n.removeLogicalChannel(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "ls":
                n = channels.Channels()
                s = n.listLogicalChannel()
                return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "stream":
                if self.inputstream != None and self.commands[3] == '-l':
                    self.upload()
                    return None

                if self.inputstream == None and self.commands[3] == '-r':
                    return self.download()

        return None

    def upload(self):
        unquoted = self.commands[4].replace("'", "").replace("\"", "")
        jailed = self.chroot.translate(unquoted)
        with io.open(jailed, 'wb') as f:
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

        return None

    def download(self):
        unquoted = self.commands[4].replace("'", "").replace("\"", "")
        jailed = self.chroot.translate(unquoted)
        f = open(jailed, "rb")
        return io.BytesIO(f.read())
