import time
import logger

from grbl import device

logging = logger.Logger()


# gently nudges the grbl serial device along to help avoid stalling in a busy loop
class Nudger:

    nudge_count = None
    nudge_logged = None
    nudge_start_time = None
    nudging = None
    device = None

    def __init__(self):

        self.nudge_count = 0
        self.nudge_logged = False
        self.nudging = False
        self.nudge_time = 0

        self.device = device.Device()

        return

    # Sets the nudge to the current time to initiate the nudging reference
    def start(self):
        self.nudge_start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
        self.nudge_count = 0
        self.nudge_logged = False
        self.nudging = True

    # If we've been stalled for more than some amount of time, we nudge the GRBL controller with a carriage return byte array
    # We reset the timer after nudging to avoid excessive nudging for long operations.
    def nudge(self):
        current_time = time.monotonic()
        elapsed_time = current_time - self.nudge_start_time
        #logging.debug("[ hc ] elapsed time: " + str(elapsed_time))

        if elapsed_time >= 2:
            self.nudge_start_time = time.monotonic()
            self.nudge_count += 1
            logging.debug("[ hc ] nudge " + str(self.nudge_count))
            self.device.write(b'\n')

    def nudged_response(self):
        if self.nudge_count > 0:
            self.nudge_logged = True
            self.nudge_count -= 1
        else:
            self.nudge_logged = False

        return self.nudge_logged

    def wait(self):
        self.start()  # Get the current time at the start to evaluate stalling and nudging
        while self.device.in_waiting() == 0:
            self.nudge()
            time.sleep(0.01)
