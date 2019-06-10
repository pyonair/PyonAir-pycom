#!/usr/bin/env python
# """
#     Wrapper classes for the Plantower PMS5003.
#     Philip Basford converted to Pycom by Steven Johnston
#     12/02/2018
# """


#from datetime import datetime, timedelta
#from serial import Serial, SerialException
from machine import UART
from machine import RTC
from strings import timestamp_template

DEFAULT_SERIAL_PINS = ('P11','P10')# pins order: (TX, RX)
DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
DEFAULT_ID = 1 #
DEFAULT_TIMEOUT = 1000

# Initialise the time
rtc = RTC()


MSG_CHAR_1 = b'\x42' # First character to be recieved in a valid packet
MSG_CHAR_2 = b'\x4d' # Second character to be recieved in a valid packet

class PlantowerReading(object):
    """
        Describes a single reading from the PMS5003 sensor
    """
    def __init__(self, line):
        """
            Takes a line from the Plantower serial port and converts it into
            an object containing the data
        """
        # self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        t = rtc.now()
        self.timestamp = timestamp_template.format(t[0], t[1], t[2], t[3], t[4], t[5])
        self.pm10_cf1 = round(line[4] * 256 + line[5], 1)
        self.pm25_cf1 = round(line[6] * 256 + line[7], 1)
        self.pm100_cf1 = round(line[8] * 256 + line[9], 1)
        self.pm10_std = round(line[10] * 256 + line[11], 1)
        self.pm25_std = round(line[12] * 256 + line[13], 1)
        self.pm100_std = round(line[14] * 256 + line[15], 1)
        self.gr03um = round(line[16] * 256 + line[17], 1)
        self.gr05um = round(line[18] * 256 + line[19], 1)
        self.gr10um = round(line[20] * 256 + line[21], 1)
        self.gr25um = round(line[22] * 256 + line[23], 1)
        self.gr50um = round(line[24] * 256 + line[25], 1)
        self.gr100um = round(line[26] * 256 + line[27], 1)

    def __str__(self):
        return (
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" %
            (self.timestamp, self.pm10_cf1, self.pm10_std, self.pm25_cf1, self.pm25_std,
             self.pm100_cf1, self.pm100_std, self.gr03um, self.gr05um,
             self.gr10um, self.gr25um, self.gr50um, self.gr100um))

class PlantowerException(Exception):
    """
        Exception to be thrown if any problems occur
    """
    pass

class Plantower():
    """
        Actual interface to the PMS5003 sensor
    """
    def __init__(self, pins=DEFAULT_SERIAL_PINS, baud=DEFAULT_BAUD_RATE, id = DEFAULT_ID):
        """
            Setup the interface for the sensor
        """

        self.pins = pins
        print("Serial pins: %s", self.pins)
        self.baud = baud
        print("Baud rate: %s", self.baud)
        self.id = id
        print("ID: %s", self.id)
        try:
            self.serial = UART(self.id, baudrate=self.baud, pins=self.pins)
            print("UART Opened Successfully")
        except SerialException as exp:
            print(str(exp))
            raise PlantowerException(str(exp))



    def _verify(self, recv):
        """
            Uses the last 2 bytes of the data packet from the Plantower sensor
            to verify that the data recived is correct
        """
        calc = 0
        ord_arr = []
        for c in bytearray(recv[:-2]): #Add all the bytes together except the checksum bytes
            calc += c
            ord_arr.append(c)
        # print(str(ord_arr))
        sent = (recv[-2] << 8) | recv[-1] # Combine the 2 bytes together
        if sent != calc:
            # print("Checksum failure %d != %d", sent, calc)
            raise PlantowerException("Checksum failure")

    def read(self, perform_flush=True):
        """
            Reads a line from the serial port and return
            if perform_flush is set to true it will flush the serial buffer
            before performing the read, otherwise, it'll just read the first
            item in the buffer
        """

        # Exit method if nothing on serial
        if not self.serial.any():
            return

        recv = self.serial.readline()
        # print(recv)


        self._verify(recv) # verify the checksum
        return PlantowerReading(recv) # convert to reading object
            #If the character isn't what we are expecting loop until timeout
        raise PlantowerException("No message recieved")
