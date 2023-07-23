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
    feed = None
    mode = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.heartbeat = False
            self.device = d.Device()
            self.nudger = n.Nudger()
            self.feed = 2000
            self.mode = "continuous"

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

            if elapsed_time >= 1/4:
                self.start_time = time.monotonic()
                self.expire_count += 1
                logging.info("[ hc ] jogger expiration ")
                if self.mode == "continuous":
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
            b'\x1b[D': lambda chunk: self.modal_execute("xleft"),
            b'\x1b[C': lambda chunk: self.modal_execute("xright"),
            b'\x1b[A': lambda chunk: self.modal_execute("yup"),
            b'\x1b[B': lambda chunk: self.modal_execute("ydown"),
            b';':      lambda chunk: self.modal_execute("zup"),
            b'/':      lambda chunk: self.modal_execute("zdown"),
            b'-':      lambda chunk: self.set_feed(-250),
            b'=':      lambda chunk: self.set_feed(250),
            b'i':      lambda chunk: self.set_mode("incremental"),
            b'c':      lambda chunk: self.set_mode("continuous")
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

    def set_mode(self, mode):
        self.mode = mode
        logging.info("[ hc ] jogger mode: " + str(self.mode))
        return self.mode

    def set_feed(self, feed):
        self.feed += feed
        if self.feed > 2000: self.feed = 2000
        if self.feed <= 0: self. feed = 1
        logging.info("[ hc ] jogger feed: " + str(self.feed))
        return self.feed

    #inches (0.001, 0.01, 0.1, 1)
    #$J=G91G21X0.0254F2000
    #$J=G91G21X0.254F2000
    #$J=G91G21X2.54F2000
    #$J=G91G21X25.4F2000

    #mm (0.1, 1, 10, 100)
    #$J=G91G21X0.1F2000
    #$J=G91G21X1F2000
    #$J=G91G21X10F2000
    #$J=G91G21X100F2000
    def modal_execute(self, axis):
        incremental = {
            "xright": b'$J=G91G21X25.4F2000\n',
            "xleft" : b'$J=G91G21X-25.4F2000\n',
            "yup"   : b'$J=G91G21Y25.4F2000\n',
            "ydown" : b'$J=G91G21Y-25.4F2000\n',
            "zup"   : b'$J=G91G21Z25.4F2000\n',
            "zdown" : b'$J=G91G21Z-25.4F2000\n'
        }

        continuous = {
            "xright": b'$J=G91 G21 X1000 F' + str(self.feed).encode() + b'\n',
            "xleft" : b'$J=G91 G21 X-1000 F' + str(self.feed).encode() + b'\n',
            "yup"   : b'$J=G91 G21 Y1000 F' + str(self.feed).encode() + b'\n',
            "ydown" : b'$J=G91 G21 Y-1000 F' + str(self.feed).encode() + b'\n',
            "zup"   : b'$J=G91 G21 Z1000 F' + str(self.feed).encode() + b'\n',
            "zdown" : b'$J=G91 G21 Z-1000 F' + str(self.feed).encode() + b'\n'
        }

        if self.mode == "continuous":
            self.execute(continuous.get(axis))
        elif self.mode == "incremental":
            self.execute(incremental.get(axis))

    def execute(self, gcode):
        if gcode is not None:
            self.put([True, gcode])
        else:
            if self.mode == "continuous":
                self.put([False, b'\n']) 
