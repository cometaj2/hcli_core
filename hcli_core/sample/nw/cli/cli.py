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
                s = n.listFreeRanges()
                return io.BytesIO(s.encode("utf-8"))

        return None
