import json
import io
import hub

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

        if self.commands[1] == "ns":
            if self.commands[2] == "ls":
                if len(self.commands) > 3:
                    h = hub.Hub()
                    n = h.listServicesInNamespace(self.commands[3])
                    return io.BytesIO(n.encode("utf-8"))
                else:
                    h = hub.Hub()
                    n = h.listNamespaces()
                    return io.BytesIO(n.encode("utf-8"))

        if self.commands[1] == "service":
            h = hub.Hub()
            n = h.findService(self.commands[2])
            return io.BytesIO(n.encode("utf-8"))

        return None
