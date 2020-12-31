import json
import io
import channels
import time

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
            if self.commands[2] == "ptt":
                if len(self.commands) > 3:
                    unquoted = self.commands[3].replace("'", "").replace("\"", "")
               	    n = channels.Channels()
                    s = n.getPttStatus(unquoted)
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "stream":
                if self.inputstream != None and self.commands[3] == '-l':
                    unquoted = self.commands[4].replace("'", "").replace("\"", "")
                    jailed = self.chroot.translate(unquoted)

                    # We do a soft form of semaphore lock using a file. This isn't intended to
                    # be perfectly fair but it should be atomic.
                    f = None
                    try:
                        f = os.open(jailed + ".lock", os.O_CREAT | os.O_EXCL)
                    except:
                        raise Exception("The channel is already being streamed to.")
                    finally:
                        if f is not None:
                            os.close(f)

                    n = channels.Channels()
                    try:
                        if not n.acquire(unquoted):
                            raise Exception("There is no such channel to stream to.")

                        self.upload(jailed)
                    finally:
                        time.sleep(3)
                        os.remove(jailed + ".lock")
                        n.release(unquoted)

                    return None

                if self.inputstream == None and self.commands[3] == '-r':
                    unquoted = self.commands[4].replace("'", "").replace("\"", "")
                    jailed = self.chroot.translate(unquoted)

                    return self.download(jailed)

        return None

    def upload(self, jailed):
        with io.open(jailed, 'wb') as f:
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)

        return None

    def download(self, jailed):
        f = open(jailed, "rb")
        return io.BytesIO(f.read())
