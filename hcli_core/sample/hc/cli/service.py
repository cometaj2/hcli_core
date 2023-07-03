import io
import os
import serial
import re
import time
import inspect
import logger
import streamer as s
import squeue as q
import filelocker as fl
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logging = logger.Logger()
logging.setLevel(logger.INFO)

device = None
scheduler = None
streamer = s.Streamer()

class Service:
    rx_buffer_size = 128
    baud_rate = 115200
    device_path = "/dev/tty.usbserial-AR0JI0GV"
    scheduler = None
    queue = None
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        global device
        global scheduler

        device = serial.Serial(self.device_path, self.baud_rate)
        #device = serial.Serial(self.device_path, self.baud_rate, timeout=1) # timeout if we want to release and retry instead of locking and waiting on device read

        self.queue = q.SQueue()
        scheduler = BackgroundScheduler()
        process = self.add_job(self.process_job_queue)
        scheduler.start()

        return

    def add_job(self, function):
        return scheduler.add_job(function, 'date', run_date=datetime.now(), max_instances=1)

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
        self.queue.clear()

        bline = b'\x18'
        device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting():
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.clear()
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

        job = self.queue.put(lambda: streamer.stream(device, streamcopy))
        logging.info("Queued jobs: " + str(self.queue.qsize()))
        return

    def clear(self):
        device.reset_input_buffer()
        device.reset_output_buffer()
        while device.inWaiting():
            response = device.read(200)

    def process_job_queue(self):

        with streamer.lock:
            while True:
                if not streamer.is_running and not self.queue.empty():
                    job = self.add_job(self.queue.get())
                    logging.info("Queued jobs: " + str(self.queue.qsize()) + ". Streaming job: " + job.id )

                time.sleep(1)
