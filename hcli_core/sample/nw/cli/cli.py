import json
import io
import networks

import os.path
from os import path

class CLI:
    commands = None
    inputstream = None
    
    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream

    def execute(self):
        print(self.commands)

        if self.commands[1] == "ls":
            if self.commands[2] == "-a":
                None
            elif self.commands[2] == "-f":
                n = networks.Networks()
                s = n.listFreeSubnets()
                return io.BytesIO(s.encode("utf-8"))
            elif self.commands[2] == "-fp":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.listFreeSubnetsWithPrefix(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))

        if self.commands[1] == "allocate":
            if self.commands[2] == "-p":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.allocateSubnet(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))

        return None
