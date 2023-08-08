import io
import re
import time
import logger
import queue as q
import threading

from grbl import device as d

logging = logger.Logger()


# Singleton GRBL controller that handles all reads and writes to and from the serial device.
class Controller:
    instance = None
    rq = None
    rrq = None
    sq = None
    srq = None
    lock = None
    realtime_thread = None
    paused = None

    def __new__(self):
        if self.instance is None:
            self.instance = super().__new__(self)

            self.device = d.Device()

            self.rq = q.Queue()  # realtime queue (for realtime commands that need to execute immediately)
            self.rrq = q.Queue() # realtime response queue

            self.sq = q.Queue()  # streaming queue (for longer standing streaming gcode thru)
            self.srq = q.Queue() # streaming response queue

            self.lock = threading.Lock()
            self.write_condition = threading.Condition()

            self.connected = False
            self.trying = False
            self.paused = False

            self.realtime_thread = threading.Thread(target=self.realtime)

        return self.instance

    def start(self):
        if not hasattr(self, 'write_thread') or not self.write_thread.is_alive():
            self.write_thread = threading.Thread(target=self.realtime)
            self.write_thread.start()

    def set(self, device_path):
        self.device.set(device_path)

    def close(self):
        self.device.close()

    def write(self, serialbytes):
        self.sq.put(serialbytes)

    def readline(self):
        return self.srq.get()

    def realtime_write(self, serialbytes):
        self.rq.put(serialbytes)

    def realtime_readline(self):
        return self.rrq.get()

    def unlock(self):
        self.realtime_write(b'$X\n')
        self.realtime_message()

    def stop(self):
        self.realtime_write(b'!')
        self.realtime_message()

    def resume(self):
        self.realtime_write(b'~')
        self.realtime_message()

    def status(self):
        self.realtime_write(b'?')
        self.realtime_message()

    def realtime_message(self):
        while self.rrq.empty():
            time.sleep(0.01)

        while not self.rrq.empty():
            response = self.realtime_readline()
            rs = response.decode()

            logging.info(rs)

            if response.find(b'error') >= 0:
                logging.info("[ hc ] " + rs + " " + error.messages[rs])

            time.sleep(0.01)

    def connect(self, device_path):
        self.connected = False
        self.trying = True

        self.set(device_path)
        logging.info("[ hc ] wake up grbl...")

        self.device.reset_input_buffer()
        self.device.reset_output_buffer()
        time.sleep(0.5)

        bline = b'\r\n\r\n'
        self.realtime_write(bline)
        time.sleep(2)

        while not self.rrq.empty():
            response = self.rrq.get()
            logging.info(response.decode())

            if response.find(b'Grbl') >= 0:
                self.connected = True

        if self.connected:
            self.realtime_write(b'$$\n')
            self.realtime_write(b'$I\n')
            self.realtime_write(b'$G\n')
            time.sleep(1)

            while not self.rrq.empty():
                response = self.rrq.get()
                logging.info(response.decode())
        else:
            self.close()

        self.trying = False
        return self.connected

    def reset(self):
        bline = b'\x18'
        self.realtime_write(bline)
        time.sleep(2)

        while not self.rrq.empty():
            response = self.realtime_readline()
            logging.info(response.decode())

        self.abort()

        return

    def abort(self):
        self.rq.queue.clear()
        self.rrq.queue.clear()
        self.sq.queue.clear()
        self.srq.queue.clear()
        self.device.abort()
        self.paused = False
        self.reset()

    # active process commands to the grbl read buffer. this is the only method that should read/write directly from/to serial grbl.
    def realtime(self):
        try:
            while True:
                if self.connected or self.trying:

                    # we give priority to realtime commands over streaming commands
                    while not self.rq.empty():
                        command = self.rq.get().strip()
                        if not (command == b'!' or command == b'~' or command == b'?'):
                            command = command + b'\n'

                        self.device.write(command)

                        if not (command == b'!' or command == b'~'):
                            while self.device.in_waiting() == 0:
                                time.sleep(0.01)

                            while self.device.in_waiting() > 0:
                                bline = self.device.readline().strip()
                                self.rrq.put(b'[ ' + command.strip() + b' ] ' + bline)

                                time.sleep(0.01)
                        else:
                            if command == b'!':
                                self.paused = True
                            elif command == b'~':
                                self.paused = False

                            self.rrq.put(b'[ hc ] ' + command + b' ok')

                    # then we process the streaming queue or continue processing it.
                    if not self.sq.empty() and not self.paused:
                        command = self.sq.get().strip()
                        if not (command == b'!' or command == b'~' or command == b'?'):
                            command = command + b'\n'

                        self.device.write(command)

                        if not (command == b'!' or command == b'~'):
                            while self.device.in_waiting() == 0:
                               time.sleep(0.01)

                            while self.device.in_waiting() > 0:
                                bline = self.device.readline().strip()
                                self.srq.put(b'[ ' + command.strip() + b' ] ' + bline)

                                time.sleep(0.01)
                        else:
                            if command == b'!':
                                self.paused = True
                            elif command == b'~':
                                self.paused = False

                            self.srq.put(b'[ hc ] ' + command + b' ok')

                time.sleep(0.01)
        except TypeError:
            logging.info("[ hc ] unable to communicate over serial port.")
        except OSError as e:
            logging.info("[ hc ] unable to communicate over serial port.")
        finally:
            pass

class TerminationException(Exception):
    pass
