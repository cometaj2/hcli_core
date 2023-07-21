import io
import re
import serial
import logger
import threading
import jobqueue as j
import immediate as i
import device as d
import nudger as n
import time
import error

logging = logger.Logger()


# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None
    device = None
    nudger = None
    terminate = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate_queue = i.Immediate()
            self.job_queue = j.JobQueue()
            self.device = d.Device()
            self.nudger = n.Nudger()
            self.exception_event = threading.Event()
            self.terminate = False

        return self.instance

    # simple g-code streaming
    def stream(self, inputstream):
        self.is_running = True
        self.terminate = False
        ins = io.StringIO(inputstream.getvalue().decode())

        try:
            for l in ins:
                line = re.sub('\s|\(.*?\)','',l).upper() # Strip comments/spaces/new line and capitalize
                self.device.write(str.encode(line + '\n')) # Send g-code block to grbl

                self.nudger.start()  # Get the current time at the start to evaluate stalling and nudging
                while self.device.inWaiting() == 0:
                    self.nudger.nudge()
                    time.sleep(0.01)

                while self.device.inWaiting() > 0:
                    if self.terminate == True:
                        raise TerminationException("[ hc ] terminate ")

                    response = self.device.readline().strip()
                    rs = response.decode()
                    if not self.nudger.logged("[ " + line + " ] " + rs):
                        logging.info("[ " + line + " ] " + rs)

                    if response.find(b'error') >= 0 or response.find(b'MSG:Reset') >= 0:
                        logging.info("[ hc ] " + rs + " " + error.messages[rs])
                        raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                    time.sleep(0.01)

                self.immediate_queue.process_immediate()
                if self.terminate == True:
                    raise TerminationException("[ hc ] terminate ")

            self.wait()

        except TerminationException as e:
            self.immediate_queue.abort()
            self.device.abort()
        except Exception as e:
            self.immediate_queue.abort()
            self.device.abort()
            self.abort()
        finally:
            self.is_running = False
            self.terminate = False

        return

    def abort(self):
        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.job_queue.clear()

        self.is_running = False
        self.terminate = False

    # we wait for idle before existing the streamer to avoid stacking up multiple jobs on top of one another (helps with non gcode jobs)
    def wait(self):
        bline = b'?'
        stop = False

        while not stop:
            self.device.write(bline)

            response = self.device.readline().strip()
            line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
            logging.debug("[ " + line + " ] " + response.decode())
            if response.find(b'<Idle|') >= 0:
               stop = True 

            time.sleep(0.1)
            self.immediate_queue.process_immediate()
            if self.terminate == True:
                raise TerminationException("[ hc ] terminate ")

class TerminationException(Exception):
    pass
