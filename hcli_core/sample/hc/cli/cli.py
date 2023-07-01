import json
import io
import os
import inspect
import sys
import glob
import serial
import io
import logger
import service
from functools import partial
from serial.tools import list_ports

logging = logger.Logger()
logging.setLevel(logger.INFO)

class CLI:
    commands = None
    inputstream = None
    service = None

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.service = service.Service()

    def execute(self):

        if len(self.commands) == 1:
            if self.inputstream is not None:

               f = io.BytesIO()
               for chunk in iter(partial(self.inputstream.read, 16384), b''):
                   f.write(chunk)

               self.service.add_job(lambda: self.service.stream(f))

            return None

        if self.commands[1] == "scan":
            scanned = json.dumps(self.scan(), indent=4) + "\n"

            return io.BytesIO(scanned.encode("utf-8"))

        if self.commands[1] == "connect":
            self.service.add_job(self.service.connect)
            return

        if self.commands[1] == "disconnect":
            self.service.add_job(self.service.disconnect)
            return

        if self.commands[1] == "reset":
            self.service.add_job(self.service.reset)

        if self.commands[1] == "stop":
            self.service.add_job(self.service.stop)

        if self.commands[1] == "resume":
            self.service.add_job(self.service.resume)

        if self.commands[1] == "device":
            if len(self.commands) > 2:
                #self.streamer.device(self.commands[2])
                pass

        return None

    def scan(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:

            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass

        return result