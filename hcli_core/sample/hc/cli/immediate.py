import io
import re
import serial
import logger
import threading
import queue as q
import time

logging = logger.Logger()
logging.setLevel(logger.INFO)

global device

# Singleton Immediate
class Immediate:
    instance = None
    is_running = False
    lock = None
    immediate_queue = None
    immediate = None
    paused = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate_queue = q.Queue()
            self.immediate = True
            self.paused = False

        return self.instance

    # we put an immediate command to be handled immediately (i.e. particularly for hold, resume and status (!, ~, ?))
    # this is intended to help avoid disrupting the serial buffer and flow of the gcode stream
    def put(self, inputstream):
        self.immediate_queue.put(inputstream.getvalue())
        return

    def process_immediate(self, device):
        try:
            while not self.immediate_queue.empty() or self.paused:
                if not self.immediate_queue.empty():
                    ins = io.BytesIO(self.immediate_queue.get())
                    sl = ins.getvalue().decode().strip()

                    bline = b''
                    if sl == '?' or sl == '!' or sl == '?':
                        bline = str.encode(sl).upper()
                    else:
                        bline = str.encode(sl + "\n").upper()

                    device.write(bline)
                    time.sleep(1)

                    line = bline.decode().strip()

                    if line == '!':
                        self.paused = True

                    if line == '!' or line == '~':
                        logging.info("[ " + line + " ] " + "ok")
                    elif line == '?':
                        response = device.readline().strip()
                        logging.info("[ " + line + " ] " + response.decode())
                    else:
                        while device.inWaiting() > 0:
                            response = device.readline().strip() # wait for grbl response
                            logging.info("[ " + line + " ] " + response.decode())

                    if line == '~':
                        self.paused = False

                time.sleep(1/5000)

        except Exception as exception:
            logging.error("[ Immediate processing ] " + str(exception))
        finally:
            self.paused = False
            self.immediate = False

        return
