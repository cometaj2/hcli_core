import io
import sys
import os
import serial
import re
import time
import inspect
import logger
import streamer as s
import squeue as q
import immediate as i
import device as d
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logging = logger.Logger()
logging.setLevel(logger.INFO)

class Service:
    device = None
    scheduler = None
    queue = None
    device = None
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        global scheduler
        global streamer

        scheduler = BackgroundScheduler()
        streamer = s.Streamer()
        self.device = d.Device()
        self.queue = q.SQueue()
        process = self.add_job(self.process_job_queue)
        scheduler.start()

        return

    def add_job(self, function):
        return scheduler.add_job(function, 'date', run_date=datetime.now(), max_instances=1)

    def connect(self, device_path):
        self.device.set(device_path)
        logging.info("[ wake up grbl... ] ")

        immediate = i.Immediate()
        immediate.immediate_queue.queue.clear()

        bline = b'\r\n\r\n'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.simple_command(io.BytesIO(b'$$'))
        self.simple_command(io.BytesIO(b'$I'))
        self.simple_command(io.BytesIO(b'$G'))

        return

    # We kick off to a deferred execution and since we cleared the job queue, shutting down executes immediately.
    def disconnect(self):
        immediate = i.Immediate()
        immediate.immediate_queue.queue.clear()
        self.queue.clear()
        scheduler.remove_all_jobs()

        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        def shutdown():
            self.clear()
            self.device.close()
            sys.exit(0)

        job = self.queue.put(lambda: shutdown())
        return

    def reset(self):
        immediate = i.Immediate()
        immediate.immediate_queue.queue.clear()
        self.queue.clear()
        scheduler.remove_all_jobs()

        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.clear()
        return

    def status(self):
        immediate = i.Immediate()
        immediate.put(io.BytesIO(b'?'))
        return

    def home(self):
        self.stream(io.BytesIO(b'$H'))
        return

    def unlock(self):
        immediate = i.Immediate()
        immediate.put(io.BytesIO(b'$X'))
        return

    def stop(self):
        immediate = i.Immediate()
        immediate.put(io.BytesIO(b'!'))
        return

    def resume(self):
        immediate = i.Immediate()
        immediate.put(io.BytesIO(b'~'))
        return

    def jobs(self):
        job_names = [job.id for job in scheduler.get_jobs()]
        print(job_names)
        return

    def simple_command(self, inputstream):
        immediate = i.Immediate()
        immediate.put(io.BytesIO(inputstream.getvalue()))
        return

    # send a streaming job to the queue
    def stream(self, inputstream):
        streamcopy = io.BytesIO(inputstream.getvalue())
        inputstream.close()

        job = self.queue.put(lambda: streamer.stream(streamcopy))
        logging.info("[ queued jobs " + str(self.queue.qsize()) + " ] ")
        return

    def clear(self):
        self.device.reset_input_buffer()
        self.device.reset_output_buffer()
        while self.device.inWaiting():
            response = device.read(200)

    # we process immediate commands first and then queued jobs in sequence
    def process_job_queue(self):
        with streamer.lock:
            immediate = i.Immediate()
            while True:
                while not streamer.is_running and not immediate.immediate_queue.empty():
                    immediate.process_immediate()
                if not streamer.is_running and not self.queue.empty():
                    job = self.add_job(self.queue.get())
                    logging.info("[ queued jobs " + str(self.queue.qsize()) + " ] streaming job: " + job.id )

                time.sleep(1)
