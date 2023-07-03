import io
import re
import serial
import logger
import threading
import time

logging = logger.Logger()
logging.setLevel(logger.INFO)

# Singleton Streamer
class Streamer:
    instance = None
    rx_buffer_size = 128
    is_running = False
    lock = None

    def __new__(cls):
        if cls.instance is None:

            cls.instance = super().__new__(cls)
            cls.lock = threading.Lock()

        return cls.instance

    # g-code streaming that keeps the GRBL serial buffer full
    def stream(self, device, inputstream):
        self.is_running = True
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
                    response = device.readline().strip()
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
                    #else:
                    #    logging.info("[ " + line + " ] " + response.decode())
                    #    g_count += 1
                    #    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

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
                #else:
                #    logging.info("[ " + line + " ] " + response.decode())
                #    g_count += 1
                #    del serial_buffer[0] # Delete the block character count corresponding to the last 'ok'

        except:
            self.clear(device)
        finally:
            time.sleep(2)
            self.is_running = False
            return

        return


    def clear(self, device):
        device.reset_input_buffer()
        device.reset_output_buffer()
        while device.inWaiting():
            response = device.read(200)
