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
            self.immediate = i.Immediate()
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
        line = ""

        try:
            for l in ins:
                line = re.sub('\s|\(.*?\)','',l).upper() # Strip comments/spaces/new line and capitalize

                # we unwrap the defered job containing controls into an immediate command execution.
                if line == '!' or line == '~' or line == '?' or line.startswith('$') or line.strip() == '':
                    self.immediate.put(inputstream)
                    break

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

                self.immediate.process_immediate()
                if self.terminate == True:
                    raise TerminationException("[ hc ] terminate ")

            self.wait(line)

        except TerminationException as e:
            self.immediate.abort()
            self.device.abort()
        except Exception as e:
            self.immediate.abort()
            self.device.abort()
            self.abort()
        finally:
            self.terminate = False
            self.is_running = False

        return

    def abort(self):
        self.job_queue.clear()

        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())


        self.is_running = False
        self.terminate = False

    # we wait for idle before existing the streamer to avoid stacking up multiple jobs on top of one another (helps with non gcode jobs)
    def wait(self, line):
        bline = b'?'
        stop = False

        while not stop:
            self.device.write(bline)

            self.nudger.start()  # Get the current time at the start to evaluate stalling and nudging
            while self.device.inWaiting() == 0:
                self.nudger.nudge()
                time.sleep(0.01)

            while self.device.inWaiting() > 0:
                if self.terminate == True:
                    raise TerminationException("[ hc ] terminate ")

                response = self.device.readline().strip()
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
                #self.device.abort()
                raise TerminationException("[ hc ] terminate ")

            time.sleep(0.2)

class TerminationException(Exception):
    pass
