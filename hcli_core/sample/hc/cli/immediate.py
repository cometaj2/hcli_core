import io
import re
import serial
import logger
import queue as q
import jobqueue as j
import device as d
import streamer as s
import time
import error

logging = logger.Logger()
logging.setLevel(logger.INFO)


# Singleton Immediate
class Immediate:
    instance = None
    immediate_queue = None
    paused = None
    nudge_count = None
    nudge_logged = None
    start_time = None
    device = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.immediate_queue = q.Queue()
            self.job_queue = j.JobQueue()
            self.paused = False
            self.nudge_count = 0
            self.nudge_logged = False
            self.device = d.Device()
            self.terminate = False

        return self.instance

    # we put an immediate command to be handled immediately (i.e. particularly for hold, resume and status (!, ~, ?))
    # this is intended to help avoid disrupting the serial buffer and flow of the gcode stream
    def put(self, inputstream):
        self.immediate_queue.put(inputstream.getvalue())
        return

    def process_immediate(self):
        try:
            self.terminate = False
            while not self.immediate_queue.empty() or self.paused:
                if not self.immediate_queue.empty():
                    ins = io.BytesIO(self.immediate_queue.get())
                    sl = ins.getvalue().decode().strip()

                    bline = b''
                    if sl == '!' or sl == '?':
                        bline = str.encode(sl).upper()
                    else:
                        bline = str.encode(sl + "\n").upper()

                    line = bline.decode().strip()
                    if not (line.startswith('$') and self.paused):
                        self.device.write(bline)

                    if line == '!':
                        logging.info("[ hc ] " + line + " " + "ok")
                        self.paused = True
                    elif (line.startswith('$') and self.paused):
                        logging.info("[ hc ] " + line + " " + "not on feed hold nor while streaming a job")
                    elif line == '?':
                        response = self.device.readline().strip()
                        logging.info("[ " + line + " ] " + response.decode())
                    else:
                        self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
                        while self.device.inWaiting() == 0:
                            self.stalled()
                            time.sleep(1)

                        while self.device.inWaiting() > 0:
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

                    if line == '~':
                        self.paused = False

                time.sleep(1/100)
                if self.terminate == True:
                    break

        except Exception as exception:
            streamer = s.Streamer()
            self.abort()
            self.device.abort()
            streamer.abort()

        finally:
            self.paused = False
            self.nudge_logged = False
            self.nudge_count = 0
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
            self.device.write(b'\n')

    def clear(self):
        return self.immediate_queue.queue.clear()

    def empty(self):
        return self.immediate_queue.empty()

    def abort(self):
        self.clear()
        self.paused = False
        self.nudge_logged = False
        self.nudge_count = 0
