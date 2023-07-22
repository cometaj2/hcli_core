import json
import io
import os
import inspect
import sys
import glob
import serial
import io
import service
from functools import partial
from serial.tools import list_ports
from collections import OrderedDict


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

               command = f.getvalue().decode().strip().upper()
               if command == '!' or command == '~' or command == '?' or command.startswith('$') or command.strip() == '':
                   self.service.simple_command(f)
               else:
                   self.service.stream(f, "sampled: " + command.splitlines()[0])

            return None

        # a named job
        elif self.commands[1] == "-j":
            if len(self.commands) > 2:
                if self.inputstream is not None:

                   f = io.BytesIO()
                   for chunk in iter(partial(self.inputstream.read, 16384), b''):
                       f.write(chunk)

                   command = f.getvalue().decode().strip().upper()
                   self.service.stream(f, self.commands[2])

                return None

        elif self.commands[1] == "scan":
            scanned = json.dumps(self.scan(), indent=4) + "\n"

            return io.BytesIO(scanned.encode("utf-8"))

        elif self.commands[1] == "connect":
            if len(self.commands) > 2:
                self.service.connect(self.commands[2])
            return

        elif self.commands[1] == "disconnect":
            self.service.disconnect()
            return

        elif self.commands[1] == "reset":
            self.service.add_job(self.service.reset)

        elif self.commands[1] == "status":
            self.service.status()

        elif self.commands[1] == "stop":
            self.service.stop()

        elif self.commands[1] == "home":
            self.service.home()

        elif self.commands[1] == "unlock":
            self.service.unlock()

        elif self.commands[1] == "resume":
            self.service.resume()

        elif self.commands[1] == "zero":
            self.service.zero()

        elif self.commands[1] == "jog":
            if self.inputstream is not None:
               self.service.jog(self.inputstream)

            return None

        elif self.commands[1] == "jobs":
            reversal = OrderedDict(sorted(self.service.jobs().items(), reverse=True))
            jobs = json.dumps(reversal, indent=4) + "\n"

            return io.BytesIO(jobs.encode("utf-8"))
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

        result = {}
        for i, port in enumerate(ports, start=1):

            try:
                s = serial.Serial(port)
                s.close()
                result[str(i)] = port
            except (OSError, serial.SerialException):
                pass

        return result
