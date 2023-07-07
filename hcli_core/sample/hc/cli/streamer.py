import io
import re
import serial
import logger
import threading
import jobqueue as j
import immediate as i
import device as d
import time

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

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.immediate_queue = i.Immediate()
            self.job_queue = j.JobQueue()
            self.nudge_count = 0
            self.nudge_logged = False
            self.device = d.Device()

        return self.instance

    # simple g-code streaming
    def stream(self, inputstream):
        self.is_running = True
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
                    response = self.device.readline().strip()
                    if self.nudge_count > 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        self.nudge_logged = True
                        self.nudge_count = 0
                    elif not self.nudge_logged:
                        logging.info("[ " + line + " ] " + response.decode())

                    if response.find(b'error') >= 0:
                        logging.info("[ hc ] gcode error " + response.decode())
                        raise Exception("[ hc ] gcode error " + response.decode())

                    time.sleep(1/100)
                self.nudge_logged = False

                self.immediate_queue.process_immediate()

        except Exception as e:
            self.cleanup()
        finally:
            time.sleep(2)
            self.nudge_count = 0
            self.nudge_logged = False
            self.is_running = False
            return

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
            logging.info("[ hc ] nudge " + str(self.nudge_count))
            self.immediate_queue.process_immediate()
            self.device.write(b'\n')

    def cleanup(self):
        self.device.reset_input_buffer()
        self.device.reset_output_buffer()
        while self.device.inWaiting():
            response = self.device.read(200)

    def abort(self):
        self.immediate_queue.clear()
        self.job_queue.clear()
        self.cleanup()

        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())
