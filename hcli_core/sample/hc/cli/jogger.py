import re
import queue as q
import device as d
import time
import logger
import queue as q
import nudger as n
import error
from functools import partial

logging = logger.Logger()


# Singleton Jogger to track jogging motion. The jogger errs on the side of caution and should stops if it's not getting a heartbeat.
class Jogger:
    instance = None
    heartbeat = None
    device = None
    is_running = None
    start_time = None
    expire_count = None
    jogger_queue = None
    jog_count = None
    nudger = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.heartbeat = False
            self.device = d.Device()
            self.nudger = n.Nudger()

            self.is_running = False

            self.expire_count = 0
            self.jog_count = 0

            self.jogger_queue = q.Queue()

        return self.instance

    def put(self, boolean):
        self.jogger_queue.put(boolean)
        return

    def empty(self):
        return self.jogger_queue.empty()

    def clear(self):
        return self.jogger_queue.queue.clear()

    def heart(self, heartbeat):
        self.heartbeat = heartbeat
        if self.heartbeat == True:
            logging.debug("[ hc ] true heart ")
            self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
            self.expire_count = 0
        elif self.heartbeat == False:
            logging.debug("[ hc ] false heart ")
            bline = b'!'
            self.device.write(bline)
            self.clear()
            self.jog_count = 0;

    def expire(self):
        if not self.heartbeat == False:
            current_time = time.monotonic()
            elapsed_time = (current_time - self.start_time)
            logging.debug(elapsed_time)

            if elapsed_time >= 1/4:
                self.start_time = time.monotonic()
                self.expire_count += 1
                logging.info("[ hc ] jogger expiration ")
                self.heart(False)
                self.is_running = False
                self.jog_count = 0;
                self.clear()

    # We intentionally try to expire by default to stop continuous jogging if no heartbeat signal has been received in awhile
    # We want to avoid crashing the CNC by waiting for a positive stop signal.
    def jog(self):
        try:
            self.is_running = True
            self.heartbeat = True

            self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging

            line = ""

            while self.is_running and self.heartbeat == True:
                if not self.jogger_queue.empty():
                    heartbeat = self.jogger_queue.get()
                    self.heart(heartbeat[0])
                    if self.heartbeat == True and self.jog_count == 0:
                        self.jog_count += 1
                        self.device.write(heartbeat[1])
                        line = heartbeat[1].decode().strip()
                        logging.info("[ hc ] " + line)

                self.expire()
                time.sleep(0.0001)

            self.nudger.start()  # Get the current time at the start to evaluate stalling and nudging
            while self.device.inWaiting() == 0:
                self.nudger.nudge()
                time.sleep(0.01)

            while self.device.inWaiting() > 0:
                response = self.device.readline().strip()
                rs = response.decode()
                if not self.nudger.logged("[ " + line + " ] " + rs):
                    logging.info("[ " + line + " ] " + rs)

                if response.find(b'error') >= 0 or response.find(b'MSG:Reset') >= 0:
                    logging.info("[ hc ] " + rs + " " + error.messages[rs])
                    raise Exception("[ hc ] " + rs + " " + error.messages[rs])

                time.sleep(0.5)

            self.device.abort()

        except Exception as e:
            self.device.abort()
            self.abort()

    def abort(self):
        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.clear()
        self.is_running = False

    # real-time jogging by continuously reading the inputstream
    def parse(self, inputstream):
        cases = {
            b'\x1b[D': lambda chunk: self.execute(b'$J=G91 G21 X-1000 F2000\n'),    # xleft
            b'\x1b[C': lambda chunk: self.execute(b'$J=G91 G21 X1000 F2000\n'),     # xright
            b'\x1b[A': lambda chunk: self.execute(b'$J=G91 G21 Y1000 F2000\n'),     # yup
            b'\x1b[B': lambda chunk: self.execute(b'$J=G91 G21 Y-1000 F2000\n'),    # ydown
            b';':      lambda chunk: self.execute(b'$J=G91 G21 Z1000 F2000\n'),     # zup
            b'/':      lambda chunk: self.execute(b'$J=G91 G21 Z-1000 F2000\n')     # zdown
        }

        for chunk in iter(partial(inputstream.read, 16384), b''):
            logging.debug("[ hc ] chunk " + str(chunk))
            first = chunk[:1]
            if first == b'\x1b':
                action = cases.get(chunk[:3], lambda chunk: None)
            else:
                action = cases.get(chunk[:1], lambda chunk: None)
            action(chunk)

            time.sleep(0.0001)

        return

    def execute(self, gcode):
        if gcode is not None:
            self.put([True, gcode])
        else:
            self.put([False, b'\n']) 
