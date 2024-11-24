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
                n = networks.Networks()
                s = n.listAllocatedNetworks()
                return io.BytesIO(s.encode("utf-8"))
            elif self.commands[2] == "-f":
                n = networks.Networks()
                s = n.listFreeNetworks()
                return io.BytesIO(s.encode("utf-8"))
            elif self.commands[2] == "-fp":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.listFreeNetworksWithPrefix(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))

        if self.commands[1] == "group":
            if self.commands[2] == "create":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.createLogicalGroup(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "mv":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.renameLogicalGroup(self.commands[3], self.commands[4])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "rm":
                if len(self.commands) > 3:
                    n = networks.Networks()
                    s = n.removeLogicalGroup(self.commands[3])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "ls":
                n = networks.Networks()
                s = n.listLogicalGroup()
                return io.BytesIO(s.encode("utf-8"))

        if self.commands[1] == "allocate":
            if self.commands[2] == "-g":
                if len(self.commands) > 5 and self.commands[4] == "-p":
                    n = networks.Networks()
                    s = n.allocateNetwork(self.commands[3], self.commands[5])
                    return io.BytesIO(s.encode("utf-8"))
                if len(self.commands) > 5 and self.commands[4] == "-n":
                    n = networks.Networks()
                    s = n.allocateSpecificNetwork(self.commands[3], self.commands[5])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "-fg":
                if len(self.commands) > 5 and self.commands[4] == "-n":
                    n = networks.Networks()
                    s = n.addSpecificFreeNetwork(self.commands[3], self.commands[5])
                    return io.BytesIO(s.encode("utf-8"))

        if self.commands[1] == "deallocate":
            if self.commands[2] == "-g":
                if len(self.commands) > 5 and self.commands[4] == "-n":
                    n = networks.Networks()
                    s = n.deallocateSpecificNetwork(self.commands[3], self.commands[5])
                    return io.BytesIO(s.encode("utf-8"))
            if self.commands[2] == "-fg":
                if len(self.commands) > 5 and self.commands[4] == "-n":
                    n = networks.Networks()
                    s = n.removeSpecificFreeNetwork(self.commands[3], self.commands[5])
                    return io.BytesIO(s.encode("utf-8"))

        return None
