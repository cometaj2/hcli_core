import io
import serial
import re
import time
import sys
import argparse
import fileinput
from functools import partial

device = None                               # Serial device

class Streamer:
    rx_buffer_size = 128
    baud_rate = 115200
    device_path = "/dev/tty.usbserial-AR0JI0GV"
    inputstream = None                          # Input stream

    def __init__(self):
        global device
        device = serial.Serial(self.device_path, self.baud_rate)

        return

    def device(self, device_path):
        self.device_path = device_path

        return

    def connect(self):
        print ("Initializing Grbl...")

        bline = b'\x18'
        device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting() > 0 :
            response = device.readline().strip() # wait for grbl response
            print ("[ " + line + " ] " + response.decode())

        device.flushInput()
        return

    def stop(self):

        bline = b'\x18'
        device.write(bline)
        time.sleep(2)

        line = re.sub('\s|\(.*?\)','',bline.decode()).upper() # Strip comments/spaces/new line and capitalize
        while device.inWaiting() > 0 :
            response = device.readline().strip() # wait for grbl response
            print ("[ " + line + " ] " + response.decode())

        return

    def stream(self, inputstream):
        self.inputstream = inputstream

        if device is None or self.inputstream is None:
            return

        time.sleep(2)

        l_count = 0

        # Send g-code program via a more agressive streaming protocol that forces characters into
        # Grbl's serial read buffer to ensure Grbl has immediate access to the next g-code command
        # rather than wait for the call-response serial protocol to finish. This is done by careful
        # counting of the number of characters sent by the streamer to Grbl and tracking Grbl's 
        # responses, such that we never overflow Grbl's serial read buffer. 
        ins = io.StringIO(self.inputstream)
        g_count = 0
        c_line = []
        for bline in ins:

            l_count += 1 # Iterate line counter
            line = re.sub('\r?\n','',bline).upper() # Strip comments/spaces/new line and capitalize
            line = line.strip()
            c_line.append(len(line)+1) # Track number of characters in grbl serial read buffer
            grbl_out = ''

            while sum(c_line) >= self.rx_buffer_size-1 | device.inWaiting() :
                response = device.readline().strip() # wait for grbl response
                print ("[ " + line + " ] " + response.decode()) # debug response
                if response.find(str.encode('ok')) >= 0 or response.find(str.encode('error')) >= 0 :
                    g_count += 1 # iterate g-code counter
                    del c_line[0] # delete the block character count corresponding to the last 'ok'

            device.write(str.encode(line + '\n')) # Send g-code block to grbl

        # Wait until all responses have been received.
        while l_count > g_count :
            response = device.readline().strip() # Wait for grbl response
            print ("[ " + line + " ] " + response.decode()) # debug response
            if response.find(str.encode('ok')) >= 0 or response.find(str.encode('error')) >= 0 :
                g_count += 1 # Iterate g-code counter
                del c_line[0] # Delete the block character count corresponding to the last 'ok'

        ins.close()
        return
