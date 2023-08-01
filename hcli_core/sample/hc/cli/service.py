import io
import json
import sys
import os
import serial
import re
import time
import inspect
import glob
import logger
import streamer as s
import jobqueue as j
import immediate as i
import device as d
import jogger as jog
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from collections import OrderedDict

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
        connected = False

        self.device.set(device_path)
        logging.info("[ hc ] wake up grbl...")

        self.immediate.clear()

        bline = b'\r\n\r\n'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\n|\r','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

            if response.find(b'Grbl') >= 0:
                connected = True

        if connected:
            self.simple_command(io.BytesIO(b'$$'))
            self.simple_command(io.BytesIO(b'$I'))
            self.simple_command(io.BytesIO(b'$G'))
        else:
            self.device.close()

        return connected

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
        self.job_queue.clear()

        bline = b'\x18'
        self.device.write(bline)
        time.sleep(2)

        line = re.sub('\n|\r','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while self.device.inWaiting() > 0:
            response = self.device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        self.streamer.terminate = True
        self.immediate.terminate = True
        self.device.abort()

        return

    def status(self):
        self.immediate.put(io.BytesIO(b'?'))
        return

    def home(self):
        home = b'$H'
        self.stream(io.BytesIO(home), home.decode())
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
        zero = b'G0 X0 Y0'
        self.stream(io.BytesIO(zero), zero.decode())

        zero = b'G0 Z0'
        self.stream(io.BytesIO(zero), zero.decode())

        status = b'?'
        self.stream(io.BytesIO(status), status.decode())
        return

    def setzeroxyz(self):
        setzero = b'G10 L20 P0 X0 Y0 Z0'
        self.stream(io.BytesIO(setzero), setzero.decode())

        status = b'?'
        self.stream(io.BytesIO(status), status.decode())

    def jobs(self):
        result = {}
        jobs = list(self.job_queue.queue.queue)
        for i, job in enumerate(jobs, start=1):
            result[str(i)] = job[0]

        reversal = OrderedDict(sorted(result.items(), reverse=True))

        if reversal.items():
            logging.info("[ hc ] ------------------------------------------")
            for key, value in reversal.items():
                logging.info("[ hc ] job " + key + ": " + value)

        return reversal

    # list serial port names
    def scan(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = {}
        for i, port in enumerate(ports, start=1):
            result[str(i)] = port

        if result.items():
            logging.info("[ hc ] ------------------------------------------")
            for key, value in result.items():
                logging.info("[ hc ] port " + key + ": " + value)

        return result

    # real-time jogging by continuously reading the inputstream
    def jog(self, inputstream):
        self.jogger.parse(inputstream)
        return

    # execution of simple commands (immediate commands (i.e. non-gcode))
    def simple_command(self, inputstream):
        self.immediate.put(io.BytesIO(inputstream.getvalue()))
        return

    # send a streaming job to the queue
    def stream(self, inputstream, jobname):
        streamcopy = io.BytesIO(inputstream.getvalue())
        inputstream.close()

        job = self.job_queue.put([jobname, lambda: self.streamer.stream(streamcopy)])
        logging.info("[ hc ] queueing job " + str(self.job_queue.qsize()) + ": " + jobname)
        return

    def tail(self):
         yield logging.tail()

    # we process immediate commands first and then queued jobs in sequence
    def process_job_queue(self):
        with self.streamer.lock:
            while True:
                while not self.streamer.is_running and not self.immediate.empty():
                    self.immediate.process_immediate()
                if not self.streamer.is_running and not self.jogger.empty():
                    self.jogger.jog()
                if not self.streamer.is_running and not self.job_queue.empty():
                    # we display all jobs in the queue for reference before streaming the next job.
                    jobs = self.jobs()

                    queuedjob = self.job_queue.get()
                    jobname = queuedjob[0]
                    lambdajob = queuedjob[1]
                    job = self.add_job(lambdajob)
                    logging.info("[ hc ] streaming " + jobname)

                time.sleep(0.1)
