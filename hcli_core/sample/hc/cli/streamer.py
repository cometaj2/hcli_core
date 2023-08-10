import io
import re
import serial
import logger
import threading
import jobqueue as j
import time
import error

from grbl import controller as c

logging = logger.Logger()


# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None
    terminate = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.job_queue = j.JobQueue()
            self.controller = c.Controller()
            self.exception_event = threading.Event()
            self.terminate = False

        return self.instance

    # simple g-code streaming
    def stream(self, inputstream):
        self.is_running = True
        self.terminate = False
        ins = io.StringIO(inputstream.getvalue().decode())
        line = ""

        try:
            for l in ins:
                l = l.split(';', 1)[0].rstrip()
                if l.rstrip('\n\r').strip() != '':
                    line = re.sub('\n|\r','',l).upper() # Strip new line carriage returns and capitalize

                    self.controller.write(str.encode(line + '\n')) # Send g-code block to grbl

                    while self.controller.srq.empty():
                        if self.terminate == True:
                            raise TerminationException("[ hc ] terminate ")
                        time.sleep(0.01)

                    while not self.controller.srq.empty():
                        if self.terminate == True:
                            raise TerminationException("[ hc ] terminate ")

                        response = self.controller.readline()
                        rs = response.decode()
                        logging.info(rs)

                        if error.match(rs):
                            raise Exception()

                        time.sleep(0.02)

                    if self.terminate == True:
                        raise TerminationException("[ hc ] terminate ")

        except TerminationException as e:
            self.abort()
        except Exception as e:
            self.abort()
        finally:
            self.terminate = False
            self.is_running = False

        return

    def abort(self):
        self.job_queue.clear()
        self.controller.reset()
        self.is_running = False
        self.terminate = False

class TerminationException(Exception):
    pass
