import io
import os
import serial
import re
import time
import inspect
import logger
import streamer as s
import queue as q
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logging = logger.Logger()
logging.setLevel(logger.INFO)

device = None

class Service:
    rx_buffer_size = 128
    baud_rate = 115200
    device_path = "/dev/tty.usbserial-AR0JI0GV"
    scheduler = None
    streamer = None
    root = os.path.dirname(inspect.getfile(lambda: None))
    queue = None

    def __init__(self):
        global device
        device = serial.Serial(self.device_path, self.baud_rate, timeout=1)
        self.streamer = s.Streamer()

        queue = q.Queue()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        return

    def add_job(self, function):
        self.scheduler.add_job(function, 'date', run_date=datetime.now(), max_instances=1)
        return

    def connect(self):
        logging.info("Initializing Grbl...")

        bline = b'\x18'
        device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting():
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.clear()
        return

    def disconnect(self):

        bline = b'\x18'
        device.write(bline)
        device.write(bline)
        device.write(bline)
        time.sleep(1)

        self.clear()
        device.close()

    def reset(self):
        self.clear()

        bline = b'\x18'
        device.write(bline)
        time.sleep(1)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting():
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        return

    def status(self):

        bline = b'?'
        device.write(bline)
        time.sleep(1)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting():
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        return

    def stop(self):

        bline = b'!'
        device.write(bline)
        logging.info("[ " + bline.decode() + " ] " + "ok")

        return

    def resume(self):

        bline = b'~'
        device.write(bline)
        logging.info("[ " + bline.decode() + " ] " + "ok")

        return

    def simple_command(self, inputstream):

        ins = io.BytesIO(inputstream.getvalue())
        sl = ins.getvalue().decode().strip()
        if sl == '!':
            self.stop()
            return
        elif sl == '~':
            self.resume()
            return
        elif sl == '?':
            self.status()
            return

        bline = str.encode(sl + '\n')
        device.write(bline)
        time.sleep(1)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting():
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        return

    # g-code streaming that keeps the GRBL serial buffer full
    def stream(self, inputstream):
        streamcopy = io.BytesIO(inputstream.getvalue())
        inputstream.close()

        self.add_job(lambda: self.streamer.stream(device, streamcopy))

    def clear(self):
        device.reset_input_buffer()
        device.reset_output_buffer()
        while device.inWaiting():
            response = device.read(200)

    def add_job_to_queue(function):
        job_queue.put(function))

    def process_job_queue():
        while True:
            if not self.queue.empty():
                function = self.queue.get()
                function
                time.sleep(1)
