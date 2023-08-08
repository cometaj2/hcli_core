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
        return self.sq.get()

    def realtime_write(self, serialbytes):
        self.rq.put(serialbytes)

    def realtime_readline(self):
        return self.rrq.get()

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

    def abort(self):
        self.device.abort()
        self.sq.queue.clear()
        self.srq.queue.clear()

    # active process commands to the grbl read buffer. this is the only method that should read/write directly from/to serial grbl.
    def realtime(self):
        try:
            while True:
                if self.connected or self.trying:

                    # we give priority to realtime commands over streaming commands
                    while not self.rq.empty():
                        command = self.rq.get()
                        self.device.write(command)
                        time.sleep(0.01)

                        while self.device.in_waiting() == 0:
                            time.sleep(0.01)

                        while self.device.in_waiting() > 0:
                            bline = self.device.readline().strip()
                            self.rrq.put(b'[ ' + command.strip() + b' ] ' + bline)

                            time.sleep(0.01)

                    # then we process the streaming queue or continue processing it.
                    if not self.sq.empty():
                        command = self.sq.get()
                        self.device.write(command)

                        while self.device.in_waiting() == 0:
                           time.sleep(0.01)

                        while self.device.in_waiting() > 0:
                            bline = self.device.readline().strip()
                            self.srq.put(b'[ ' + command.strip() + b' ] ' + bline)

                            time.sleep(0.01)

                time.sleep(0.01)
        except TypeError:
            logging.info("[ hc ] unable to connect.")
        except OSError as e:
            logging.info("[ hc ] unable to connect.")
        finally:
            pass

class TerminationException(Exception):
    pass
