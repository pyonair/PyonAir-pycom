"""
    Wrapper classes for the Plantower PMS5003.
    Philip Basford
    12/02/2018
    Converted into Pycom library by Daniel Hausner, 20/06/2019
"""

from plantowerpycom import logging
import time
from machine import Timer, UART

timestamp_template = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"  # yyyy-mm-dd hh-mm-ss

DEFAULT_SERIAL_PINS = ('P10', 'P11')  # Serial pins to use if no other specified, (TX, RX)
DEFAULT_BAUD_RATE = 9600  # Serial baud rate to use if no other specified
DEFAULT_SERIAL_TIMEOUT = 2  # Serial timeout to use if not specified
DEFAULT_READ_TIMEOUT = 1  # How long to sit looking for the correct character sequence.
DEFAULT_ID = 1  # UART bus id

DEFAULT_LOGGING_LEVEL = logging.WARN

MSG_CHAR_1 = b'\x42'  # First character to be received in a valid packet
MSG_CHAR_2 = b'\x4d'  # Second character to be received in a valid packet


class PlantowerReading(object):
    """
        Describes a single reading from the PMS5003 sensor
    """

    def __init__(self, line):
        """
            Takes a line from the Plantower serial port and converts it into
            an object containing the data
        """
        self.timestamp = timestamp_template.format(*time.gmtime())
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


class Plantower(object):
    """
        Actual interface to the PMS5003 sensor
    """

    def __init__(
            self,
            pins=DEFAULT_SERIAL_PINS,
            baud=DEFAULT_BAUD_RATE,
            serial_timeout=DEFAULT_SERIAL_TIMEOUT,
            read_timeout=DEFAULT_READ_TIMEOUT,
            log_level=DEFAULT_LOGGING_LEVEL,
            id=DEFAULT_ID
    ):
        """
            Setup the interface for the sensor
        """
        self.logger = logging.getLogger("PMS5003 Interface")
        logging.basicConfig()
        # logging.basicConfig(
        #     format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        self.logger.setLevel(log_level)
        self.pins = pins
        self.logger.info("Serial pins: %s", self.pins)
        self.baud = baud
        self.logger.info("Baud rate: %s", self.baud)
        self.serial_timeout = serial_timeout
        self.logger.info("Serial Timeout: %s", self.serial_timeout)
        self.read_timeout = read_timeout
        self.logger.info("Read Timeout: %s", self.read_timeout)
        self.id = id
        self.chrono = Timer.Chrono()
        try:
            self.serial = UART(
                self.id,
                baudrate=self.baud,
                pins=self.pins,
                timeout_chars=self.serial_timeout
            )
            self.logger.debug("Port Opened Successfully")
        except Exception as exp:
            self.logger.error(str(exp))
            raise PlantowerException(str(exp))

    def set_log_level(self, log_level):
        """
            Enables the class logging level to be changed after it's created
        """
        self.logger.setLevel(log_level)

    def _verify(self, recv):
        """
            Uses the last 2 bytes of the data packet from the Plantower sensor
            to verify that the data received is correct
        """
        calc = 0
        ord_arr = []
        for c in bytearray(recv[:-2]):  # Add all the bytes together except the checksum bytes
            calc += c
            ord_arr.append(c)
        self.logger.debug(str(ord_arr))
        sent = (recv[-2] << 8) | recv[-1]  # Combine the 2 bytes together
        if sent != calc:
            self.logger.error("Checksum failure %d != %d", sent, calc)
            raise PlantowerException("Checksum failure")

    def read(self):
        """
            Reads a line from the serial port and return
            if perform_flush is set to true it will flush the serial buffer
            before performing the read, otherwise, it'll just read the first
            item in the buffer
        """
        recv = b''
        read_timeout = self.read_timeout
        chrono = self.chrono
        chrono.reset()  # Reset the timer
        chrono.start()  # Start timer
        while (chrono.read() < read_timeout):
            inp = self.serial.read(1)  # Read a character from the input
            if inp == MSG_CHAR_1:  # check it matches
                recv += inp  # if it does add it to receive string
                inp = self.serial.read(1)  # read the next character
                if inp == MSG_CHAR_2:  # check it's what's expected
                    recv += inp  # att it to the receive string
                    recv += self.serial.read(30)  # read the remaining 30 bytes
                    self._verify(recv)  # verify the checksum
                    chrono.stop()  # Stop the timer
                    return PlantowerReading(recv)  # convert to reading object
            # If the character isn't what we are expecting loop until timeout
        chrono.stop()  # Stop the timer (in case the while loop timed out)

        raise PlantowerException("No message received")
