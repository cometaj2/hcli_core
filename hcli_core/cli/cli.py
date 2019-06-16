import json
import io

class CLI:
    commands = None
    inputstream = None
    
    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream

    def execute(self):

        if self.inputstream != None and self.commands[2] == '-l':
            self.upload()
            return None

        if self.inputstream == None and self.commands[2] == '-r':
            return self.download()

    def upload(self):
        with io.open(self.commands[3].replace("'", ""), 'wb') as f:
            f.write(self.inputstream)
            return None

    def download(self):
        f = open(self.commands[3].replace("'", ""), "rb")
        return io.BytesIO(f.read())
