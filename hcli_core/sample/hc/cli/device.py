import serial
import logger

logging = logger.Logger()
logging.setLevel(logger.INFO)


# Singleton device for serial port access
class Device:
    instance = None
    rx_buffer_size = 128
    baud_rate = 115200
    device_path = "/dev/tty.usbserial-AR0JI0GV"
    device = None

    def __new__(self):
        if self.instance is None:
            self.instance = super().__new__(self)

        return self.instance

    def set(self, device_path):
        self.device_path = device_path.strip('"')
        self.device = serial.Serial(self.device_path, self.baud_rate, timeout=1)
        logging.info("[ hc ] connected to " + self.device_path)

    def write(self, serialbytes):
        self.device.write(serialbytes)
        return

    def readline(self):
        return self.device.readline()

    def inWaiting(self):
        return self.device.inWaiting()

    def read(self, bytecount):
        return self.device.read(bytecount)

    def reset_input_buffer(self):
        return self.device.reset_input_buffer()

    def reset_output_buffer(self):
        return self.device.reset_output_buffer()

    def close(self):
        return self.device.close()

    def abort(self):
        self.device.reset_input_buffer()
        self.device.reset_output_buffer()
