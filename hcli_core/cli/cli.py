import json
import io

class CLI:
    commands = None
    inputstream = None

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream

    def execute(self):
        if self.commands[1] == "--version":
            return io.BytesIO(b"1.0.2")

        if self.commands[1] == "go":
            return self.pretty(self.inputstream)

        return None

    def pretty(self, inputstream):
        if self.inputstream != None:
            try:
                string = json.loads(self.inputstream.read().decode("utf-8"))
                j = json.dumps(string, indent=4)
                return io.BytesIO(j.encode("utf-8"))
            except:
                return None

        return None
