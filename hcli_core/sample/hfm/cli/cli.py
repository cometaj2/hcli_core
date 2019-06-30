import json
import io
import os
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

        if self.commands[1] == "cp":
            if self.inputstream != None and self.commands[2] == '-l':
                self.upload()
                return None

            if self.inputstream == None and self.commands[2] == '-r':
                return self.download()

        if self.commands[1] == "ls":
            content = bytearray(b'')

            ls = subprocess.Popen(["ls", "-la", self.chroot.pwd], stdout=subprocess.PIPE,)            
            pipe = ls.stdout

            for line in pipe:
                content.extend(line)

            return io.BytesIO(content)

    def upload(self):
        unquoted = self.commands[3].replace("'", "").replace("\"", "")
        jailed = self.chroot.translate(unquoted)
        with io.open(jailed, 'wb') as f:
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

        return None

    def download(self):
        unquoted = self.commands[3].replace("'", "").replace("\"", "")
        jailed = self.chroot.translate(unquoted)
        f = open(jailed, "rb")
        return io.BytesIO(f.read())
