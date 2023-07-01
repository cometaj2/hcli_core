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
        device = serial.Serial(self.device_path, self.baud_rate)

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
        while device.inWaiting() > 0 :
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        device.reset_input_buffer()
        device.reset_output_buffer()
        return

    def disconnect(self):

        bline = b'\x18'
        device.write(bline)
        device.reset_input_buffer()
        device.reset_output_buffer()
        device.close()

    def reset(self):

        device.reset_input_buffer()
        device.reset_output_buffer()

        bline = b'\x18'
        device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting() > 0 :
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        return

    def status(self):

        bline = b'?'
        device.write(bline)
        time.sleep(2)
     
        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting() > 0 :
            response = device.readline().strip() # wait for grbl response
            logging.info("[ " + line + " ] " + response.decode())

        return

    def stop(self):

        bline = b'!'
        device.write(bline)

        return

    def resume(self):

        bline = b'~'
        device.write(bline)

        return

    def stream(self, inputstream):
        device.reset_input_buffer()
        device.reset_output_buffer()

        l_count = 0

        # Send g-code program via a more agressive streaming protocol that forces characters into
        # Grbl's serial read buffer to ensure Grbl has immediate access to the next g-code command
        # rather than wait for the call-response serial protocol to finish. This is done by careful
        # counting of the number of characters sent by the streamer to Grbl and tracking Grbl's 
        # responses, such that we never overflow Grbl's serial read buffer. 
        ins = io.StringIO(inputstream.getvalue().decode())
        g_count = 0
        serial_buffer = []

        try:
            for bline in ins:
                l_count += 1 # Iterate line counter
                line = re.sub('\s|\(.*?\)','',bline).upper() # Strip comments/spaces/new line and capitalize
                #line = line.strip()
                serial_buffer.append(len(line)+1) # Track number of characters in grbl serial read buffer
                grbl_out = ''

                while sum(serial_buffer) >= self.rx_buffer_size-1 | device.inWaiting():
                    response = device.readline().strip() # wait for grbl response 
                    if response.find(str.encode('ok')) >= 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1 # Iterate g-code counter
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                    elif response.find(str.encode('ok')) < 0 and response.find(str.encode('error')) < 0:
                        logging.info("[ " + line + " ] " + response.decode())
                    elif response.find(str.encode('error')) >= 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1 # Iterate g-code counter
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                        raise Exception("error")
                    elif response.find(str.encode('ok')) < 0:
                        logging.info("[ " + line + " ] " + response.decode())
                        g_count += 1 # Iterate g-code counter
                        del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

                device.write(str.encode(line + '\n')) # Send g-code block to grbl

            # Wait until all responses have been received.
            while l_count > g_count:
                response = device.readline().strip() # Wait for grbl response
                if response.find(str.encode('ok')) >= 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1 # Iterate g-code counter
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                if response.find(str.encode('ok')) < 0 and response.find(str.encode('error')) < 0:
                    logging.info("[ " + line + " ] " + response.decode())
                elif response.find(str.encode('error')) >= 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1 # Iterate g-code counter
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'
                    raise Exception("error")
                elif response.find(str.encode('ok')) < 0:
                    logging.info("[ " + line + " ] " + response.decode())
                    g_count += 1 # Iterate g-code counter
                    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

        except:
            device.reset_input_buffer()
            device.reset_output_buffer()
            while device.inWaiting() > 0:
                response = device.readline().strip()
