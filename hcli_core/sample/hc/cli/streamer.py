import io
import re
import serial
import logger
import threading
import jobqueue as j
import immediate as i
import time
import error

from grbl import controller as c
from grbl import nudger as n

logging = logger.Logger()


# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None
    nudger = None
    terminate = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate = i.Immediate()
            self.job_queue = j.JobQueue()
            self.controller = c.Controller()
            self.nudger = n.Nudger()
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

                    while not self.controller.srq.empty():
                        if self.terminate == True:
                            raise TerminationException("[ hc ] terminate ")

                        response = self.controller.readline().strip()
                        rs = response.decode()
                        logging.info(rs)

                        if response.find(b'error') >= 0 or response.find(b'MSG:Reset') >= 0:
                            logging.info("[ hc ] " + rs + " " + error.messages[rs])
                            raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                        time.sleep(0.01)

                    if self.terminate == True:
                        raise TerminationException("[ hc ] terminate ")

            #self.wait(line)

        except TerminationException as e:
            self.immediate.abort()
            self.controller.abort()
        except Exception as e:
            self.immediate.abort()
            self.controller.abort()
            self.abort()
        finally:
            self.terminate = False
            self.is_running = False

        return

    def abort(self):
        self.job_queue.clear()

        bline = b'\x18'
        self.controller.realtime_write(bline)
        time.sleep(2)

        while not self.controller.rrq.empty():
            response = self.controller.readline().strip() # wait for grbl response
            logging.info(response.decode())

        self.is_running = False
        self.terminate = False

    # we wait for idle before existing the streamer to avoid stacking up multiple jobs on top of one another (helps with non gcode jobs)
    def wait(self, line):
        bline = b'?'
        stop = False

        while not stop:
            self.controller.write(bline)

            self.nudger.wait()  # Get the current time at the start to evaluate stalling and nudging

            while not self.controller.srq.empty():
                if self.terminate == True:
                    raise TerminationException("[ hc ] terminate ")

                response = self.controller.readline().strip()
                rs = response.decode()

                if response.find(b'<Idle|') >= 0 or response.find(b'<Check|') >= 0:
                    stop = True

                if response.find(b'|Bf:') < 0 and response.find(b'|FS:') < 0:
                    logging.info("[ " + line + " ] " + response.decode())

                if response.find(b'error') >= 0 or response.find(b'MSG:Reset') >= 0:
                    logging.info("[ hc ] " + rs + " " + error.messages[rs])
                    raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                time.sleep(0.01)

            self.immediate.process_immediate()
            if self.terminate == True:
                raise TerminationException("[ hc ] terminate ")

            time.sleep(0.2)

class TerminationException(Exception):
    pass
