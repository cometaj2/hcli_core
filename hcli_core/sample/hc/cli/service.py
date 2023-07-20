import io
import json
import sys
import os
import serial
import re
import time
import inspect
import logger
import streamer as s
import jobqueue as j
import immediate as i
import device as d
import jogger as jog
from datetime import datetime
from functools import partial
from apscheduler.schedulers.background import BackgroundScheduler

logging = logger.Logger()
logging.setLevel(logger.INFO)


class Service:
    device = None
    scheduler = None
    device = None
    jogger = None
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        global scheduler

        scheduler = BackgroundScheduler()
        self.streamer = s.Streamer()
        self.immediate = i.Immediate()
        self.job_queue = j.JobQueue()
        self.device = d.Device()
        self.jogger = jog.Jogger()
        process = self.add_job(self.process_job_queue)
        scheduler.start()

        return

    def add_job(self, function):
        return scheduler.add_job(function, 'date', run_date=datetime.now(), max_instances=1)

    def connect(self, device_path):
        self.device.set(device_path)
        logging.info("[ hc ] wake up grbl...")

        self.immediate.clear()

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

    # We cleanup the queues and disconnect by issuing an immediate shut down function execution.
    def disconnect(self):
        self.device.abort()
        self.immediate.abort()
        self.job_queue.clear()

        def shutdown():
            self.device.close()
            sys.exit(0)

        job = self.add_job(lambda: shutdown())
        return

    def reset(self):
        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.streamer.terminate = True
        self.immediate.terminate = True

        return

    def status(self):
        self.immediate.put(io.BytesIO(b'?'))
        return

    def home(self):
        self.immediate.put(io.BytesIO(b'$H'))
        return

    def unlock(self):
        self.immediate.put(io.BytesIO(b'$X'))
        return

    def stop(self):
        self.immediate.put(io.BytesIO(b'!'))
        return

    def resume(self):
        self.immediate.put(io.BytesIO(b'~'))
        return

    def zero(self):
        zero = b'G00 X0 Y0 Z0'
        self.stream(io.BytesIO(zero), "sampled: " + str(zero))
        return

    def jobs(self):
        result = {}
        jobs = list(self.job_queue.queue.queue)
        for i, job in enumerate(jobs, start=1):
            result[str(i)] = job[0]

        return result

    # real-time jogging by continuously reading the inputstream
    def jog(self, inputstream):
        cases = {
            b'\x1b[D': lambda chunk: self.compress(chunk, b'\x1b[D', b'$J=G91 G21 X-1000 F2000\n'),    # xleft
            b'\x1b[C': lambda chunk: self.compress(chunk, b'\x1b[C', b'$J=G91 G21 X1000 F2000\n'),     # xright
            b'\x1b[A': lambda chunk: self.compress(chunk, b'\x1b[A', b'$J=G91 G21 Y1000 F2000\n'),     # yup
            b'\x1b[B': lambda chunk: self.compress(chunk, b'\x1b[B', b'$J=G91 G21 Y-1000 F2000\n'),    # ydown
            b';':      lambda chunk: self.compress(chunk, b';', b'$J=G91 G21 Z1000 F2000\n'),          # zup
            b'/':      lambda chunk: self.compress(chunk, b'/', b'$J=G91 G21 Z-1000 F2000\n')          # zdown
        }

        for chunk in iter(partial(inputstream.read, 16384), b''):
            logging.info("[ hc ] chunk " + str(chunk))
            first = chunk[:1]
            if first == b'\x1b':
                action = cases.get(chunk[:3], lambda chunk: None)
            else:
                action = cases.get(chunk[:1], lambda chunk: None)
            action(chunk)

            time.sleep(0.0001)

        return

    def compress(self, chunk, code, gcode):
        chunk = chunk[len(code):]
        while chunk.startswith(code):
            chunk = chunk[len(code):]
        if gcode is not None:
            self.jogger.put([True, gcode])
        else:
            self.jogger.put([False, b'\n'])

    def simple_command(self, inputstream):
        self.immediate.put(io.BytesIO(inputstream.getvalue()))
        return

    # send a streaming job to the queue
    def stream(self, inputstream, jobname):
        streamcopy = io.BytesIO(inputstream.getvalue())
        inputstream.close()

        job = self.job_queue.put([jobname, lambda: self.streamer.stream(streamcopy)])
        logging.info("[ hc ] queued jobs " + str(self.job_queue.qsize()) + ". " + jobname)
        return

    # we process immediate commands first and then queued jobs in sequence
    def process_job_queue(self):
        with self.streamer.lock:
            while True:
                while not self.streamer.is_running and not self.immediate.empty():
                    self.immediate.process_immediate()
                if not self.streamer.is_running and not self.jogger.empty():
                    self.jogger.jog()
                if not self.streamer.is_running and not self.job_queue.empty():
                    queuedjob = self.job_queue.get()
                    jobname = queuedjob[0]
                    lambdajob = queuedjob[1]
                    job = self.add_job(lambdajob)
                    logging.info("[ hc ] queued jobs " + str(self.job_queue.qsize()) + ". streaming " + jobname )

                time.sleep(0.1)
