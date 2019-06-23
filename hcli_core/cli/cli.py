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
                if not path.exists("cli/services.json"):
                    with open("cli/services.json", "w") as f:
                        h = hub.Hub()
                        f.write(h.serialize())
                        f.close()
         
                else: 
                    with open("cli/services.json", "r") as f:
                        data = f.read()

                        f.close()
                        return io.BytesIO(data.encode("utf-8"))

        return None
