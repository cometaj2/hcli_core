import json
import io
from functools import partial

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
            for chunk in iter(partial(self.inputstream.read, 16384), b''):
                f.write(chunk)
            
            #while True:
            #    chunk = self.inputstream.read(16384)
            #    if not chunk:
            #        break
#
#                f.write(chunk)

        return None

    def download(self):
        f = open(self.commands[3].replace("'", ""), "rb")
        return io.BytesIO(f.read())

#class nbstdin:
#    stream = None
#
#    def __init__(self, stream):
#        self.stream = stream
#
#    def read(self):
#        while True:
#            chunk = req.stream.read(16384)
#            if chunk:
#                yield chunk
#            else:
#                break    

#class nbstdin:
#    stream = None
#
#    def __init__(self, stream):
#        self.stream = stream
#
#    def read(self):
#        fd = self.stream.fileno()
#        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
#        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
#
#        fis = os.fdopen(fd, 'rb', 0)
#        with fis as openfileobject:
#            for chunk in iter(partial(openfileobject.read, 16384), b''):
#                yield chunk
