import io
import os
import serial
import re
import time
import inspect
import logger
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
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        global device
        device = serial.Serial(self.device_path, self.baud_rate, timeout=1)

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
        #self.clear()

        ins = io.StringIO(inputstream.getvalue().decode())

        l_count = 0 # line counter
        g_count = 0 # g-code counter
        serial_buffer = []
        try:
            for l in ins:
                l_count += 1 # Iterate line counter
                line = re.sub('\s|\(.*?\)','',l).upper() # Strip comments/spaces/new line and capitalize
                serial_buffer.append(len(line)+1) # Track number of characters in grbl serial read buffer
                grbl_out = ''

                while sum(serial_buffer) >= self.rx_buffer_size-1 | device.inWaiting():
                    response = device.readline.strip()
                    if response.find(str.encode('ok')) >= 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                    elif response.find(str.encode('ok')) < 0 and response.find(str.encode('error')) < 0:
                        logging.info("[ " + line + " ] " + response.decode())
                    elif response.find(str.encode('error')) >= 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                        raise Exception("error")
                    elif response.find(str.encode('ok')) < 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

                device.write(str.encode(line + '\n')) # Send g-code block to grbl

            # Wait until all responses have been received.
            while l_count > g_count:
                response = device.readline().strip()
                if response.find(str.encode('ok')) >= 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                if response.find(str.encode('ok')) < 0 and response.find(str.encode('error')) < 0:
                    logging.info("[ " + line + " ] " + response.decode())
                elif response.find(str.encode('error')) >= 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                    raise Exception("error")
                elif response.find(str.encode('ok')) < 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

        except:
            self.clear()

    def clear(self):
        device.reset_input_buffer()
        device.reset_output_buffer()
        while device.inWaiting():
            response = device.read(100)
