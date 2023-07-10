import io
import re
import serial
import logger
import threading
import jobqueue as j
import immediate as i
import device as d
import time
import error

logging = logger.Logger()
logging.setLevel(logger.INFO)


# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None
    start_time = None
    nudge_count = None
    nudge_logged = None
    device = None
    terminate = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate_queue = i.Immediate()
            self.job_queue = j.JobQueue()
            self.nudge_count = 0
            self.nudge_logged = False
            self.device = d.Device()
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

                self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
                while self.device.inWaiting() == 0:
                    self.stalled()
                    time.sleep(1/100)

                while self.device.inWaiting() > 0:
                    if self.terminate == True:
                        raise TerminationException("[ hc ] terminate ")

                    response = self.device.readline().strip()
                    rs = response.decode()
                    if self.nudge_count > 0:
                        logging.info("[ " + line + " ] " + rs)
                        self.nudge_logged = True
                        self.nudge_count = 0
                    elif not self.nudge_logged:
                        logging.info("[ " + line + " ] " + rs)

                    if response.find(b'error') >= 0:
                        logging.info("[ hc ] " + rs + " " + error.messages[rs])
                        raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                    time.sleep(1/100)
                self.nudge_logged = False

                self.immediate_queue.process_immediate()
                if self.terminate == True:
                    raise TerminationException("[ hc ] terminate ")

        except TerminationException as e:
            self.immediate_queue.abort()
            self.device.abort()
        except Exception as e:
            self.immediate_queue.abort()
            self.device.abort()
            self.abort()
        finally:
            time.sleep(2)
            self.nudge_count = 0
            self.nudge_logged = False
            self.is_running = False
            self.terminate = False

        return

    # If we've been stalled for more than some amount of time, we nudge the GRBL controller with a carriage return byte array
    # We reset the timer after nudging to avoid excessive nudging for long operations.
    def stalled(self):
        current_time = time.monotonic()
        elapsed_time = current_time - self.start_time
        logging.debug(elapsed_time)

        if elapsed_time >= 2:
            self.start_time = time.monotonic()
            self.nudge_count += 1
            logging.debug("[ hc ] nudge " + str(self.nudge_count))
            self.immediate_queue.process_immediate()
            self.device.write(b'\n')

    def abort(self):
        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.job_queue.clear()

        self.nudge_count = 0
        self.nudge_logged = False
        self.is_running = False
        self.terminate = False


class TerminationException(Exception):
    pass
