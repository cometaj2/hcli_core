import io
import re
import serial
import logger
import threading
import queue as q
import time

logging = logger.Logger()
logging.setLevel(logger.INFO)

# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None
    immediate_queue = None
    immediate = None
    paused = None
    start_time = None
    nudge_count = None
    nudge_logged = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate_queue = q.Queue()
            self.immediate = True
            self.paused = False
            self.nudge_count = 0
            self.nudge_logged = False

        return self.instance

    # we toss an immediate command to be handled by the gcode stream (i.e. for hold, resume and status (!, ~, ?))
    # this is intended to help avoid disrupting the serial buffer and flow of the gcode stream
    def put(self, inputstream):
        self.immediate_queue.put(inputstream.getvalue())
        return

    # simple g-code streaming
    def stream(self, device, inputstream):
        self.is_running = True
        ins = io.StringIO(inputstream.getvalue().decode())

        try:
            for l in ins:

                line = re.sub('\s|\(.*?\)','',l).upper() # Strip comments/spaces/new line and capitalize
                device.write(str.encode(line + '\n')) # Send g-code block to grbl

                self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
                while device.inWaiting() == 0:
                    self.stalled(device)
                    time.sleep(1/100)

                while device.inWaiting() > 0:
                    response = device.readline().strip()
                    if self.nudge_count > 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        self.nudge_logged = True
                        self.nudge_count = 0
                    elif not self.nudge_logged:
                        logging.info("[ " + line + " ] " + response.decode())

                    time.sleep(1/100)
                self.nudge_logged = False

                self.process_immediate(device)

        except:
            self.clear(device)
        finally:
            time.sleep(2)
            self.nudge_count = 0
            self.immediate = False
            self.nudge_logged = False
            self.is_running = False
            return

        return

    def process_immediate(self, device):

        try:
            if not self.immediate_queue.empty():
                self.immediate = True

                while self.immediate:
                    if not self.immediate_queue.empty():
                        ins = io.BytesIO(self.immediate_queue.get())
                        sl = ins.getvalue().decode().strip()

                        device.write(str.encode(sl)) # Send g-code block to grbl

                        if sl == '!':
                            self.paused = True

                        if sl != '?':
                            logging.info("[ " + sl + " ] " + "ok")

                        if sl == '?':
                            response = device.readline().strip()
                            logging.info("[ " + sl + " ] " + response.decode())
                            if not self.paused:
                                self.immediate = False

                        if sl == '~':
                            self.immediate = False

                    time.sleep(1/5000)

        except Exception as error:
            logging.error(error)
        finally:
            self.paused = False
            self.immediate = False

        return

    # If we've been stalled for more than some amount of time, we nudge the GRBL controller with an empty byte array
    # We reset the timer after nudging to avoid excessive nudging for long operations.
    def stalled(self, device):
        current_time = time.monotonic()
        elapsed_time = current_time - self.start_time
        logging.debug(elapsed_time)

        if elapsed_time >= 2:
            self.start_time = time.monotonic()
            self.nudge_count += 1
            logging.info("[ Nudge ] " + str(self.nudge_count))
            device.write(b'\n')

    def clear(self, device):
        device.reset_input_buffer()
        device.reset_output_buffer()
        while device.inWaiting():
            response = device.read(200)
