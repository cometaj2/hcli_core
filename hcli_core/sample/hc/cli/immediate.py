import io
import re
import serial
import logger
import queue as q
import jobqueue as j
import device as d
import streamer as s
import nudger as n
import time
import error

logging = logger.Logger()


# Singleton Immediate
class Immediate:
    instance = None
    immediate_queue = None
    paused = None
    device = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.immediate_queue = q.Queue()
            self.job_queue = j.JobQueue()
            self.paused = False
            self.nudger = n.Nudger()
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
                        self.nudger.start()  # Get the current time at the start to evaluate stalling and nudging
                        while self.device.inWaiting() == 0:
                            self.nudger.nudge()
                            time.sleep(0.01)

                        while self.device.inWaiting() > 0:
                            response = self.device.readline().strip()
                            rs = response.decode()
                            if not self.nudger.logged("[ " + line + " ] " + rs):
                                logging.info("[ " + line + " ] " + rs)

                            if response.find(b'error') >= 0:
                                logging.info("[ hc ] " + rs + " " + error.messages[rs])
                                raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                            time.sleep(0.01)

                    if line == '~':
                        self.paused = False

                time.sleep(0.01)
                if self.terminate == True:
                    break

        except Exception as exception:
            streamer = s.Streamer()
            self.abort()
            self.device.abort()
            streamer.abort()

        finally:
            self.paused = False
            self.terminate = False

        return

    def clear(self):
        return self.immediate_queue.queue.clear()

    def empty(self):
        return self.immediate_queue.empty()

    def abort(self):
        self.clear()
        self.paused = False
