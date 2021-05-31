"""
    Wrapper classes for the Honeywell HPMA115S0.
    Florentin Bulot
    15/01/2019
    based on https://github.com/FEEprojects/plantower

    Converted into Pycom library by Peter Varga, 07/08/2019
"""

from sensirionpycom import logging
from machine import Timer, UART
import struct
import time

from sensirionpycom.sensirion_error_codes import ERROR_CODE_NO_ERROR, lookup_error_code

timestamp_template = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"  # yyyy-mm-dd hh-mm-ss

DEFAULT_SERIAL_PINS = ('P3', 'P17') # Serial port to use if no other specified
DEFAULT_BAUD_RATE = 115200 # Serial baud rate to use if no other specified
DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
DEFAULT_READ_TIMEOUT = 1 #How long to sit looking for the correct character sequence.
DEFAULT_ID = 1  # UART bus id

DEFAULT_LOGGING_LEVEL = logging.WARN
DEFAULT_RETRY_COUNT = 3
RETRY_SLEEP = 2
MSG_START_STOP = b'\x7e'

CMD_ADDR = b'\x00'
CMD_START_MEASUREMENT = b'\x00' #Execute
CMD_STOP_MEASUREMENT = b'\x01' #Execute
CMD_READ_MEASUREMENT = b'\x03' #Read
CMD_READ_WRITE_AUTOCLEAN_INTERVAL = b'\x80' #Read/Write
CMD_START_FAN_CLEANING = b'\x56' #Execute
CMD_DEVICE_INFORMATION = b'\xd0' #Read
CMD_RESET = b'\xd3' #Execute


SUBCMD_START_MEASUREMENT_1 = b'\x01'
SUBCMD_START_MEASUREMENT_2 = b'\x03'

SUBCMD_DEVICE_NAME = b'\x01'
SUBCMD_ARTICLE_CODE = b'\x02'
SUBCMD_SERIAL_NO = b'\x03'

SUBCMD_READ_INTERVAL = b'\x00'
SUBCMD_WRITE_INTERVAL = b'\x00'

RX_DELAY_S = 0.02 # How long to wait between sending the read command and getting data (seconds)

MIN_SAMPLE_INTERVAL = 0

class SensirionReading(object):
    """
        Describes a single reading from the Sensirion sensor
    """
    def __init__(self, line):
        """
            Takes a line from the Sensirion serial port and converts it into
            an object containing the data
        """
        if len(line) < 46:
            raise SensirionException("Data too short to parse")
        self.timestamp = timestamp_template.format(*time.gmtime())
        self.pm1 = round(struct.unpack('>f', line[5:9])[0], 1)
        self.pm25 = round(struct.unpack('>f', line[9:13])[0], 1)
        self.pm4 = round(struct.unpack('>f', line[13:17])[0], 1)
        self.pm10 = round(struct.unpack('>f', line[17:21])[0], 1)
        self.n05 = round(struct.unpack('>f', line[21:25])[0], 1)
        self.n1 = round(struct.unpack('>f', line[25:29])[0], 1)
        self.n25 = round(struct.unpack('>f', line[29:33])[0], 1)
        self.n4 = round(struct.unpack('>f', line[33:37])[0], 1)
        self.n10 = round(struct.unpack('>f', line[37:41])[0], 1)
        self.tps = round(struct.unpack('>f', line[41:45])[0], 1)

    def __str__(self):
        return (
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
            (self.timestamp, self.pm1, self.pm25,
             self.pm4, self.pm10, self.n05,
             self.n1, self.n25, self.n4,
             self.n10, self.tps))

class SensirionException(Exception):
    """
        Exception to be thrown if any problems occur
    """
    pass

class Sensirion(object):
    """
        Actual interface to the Sensirion SPS030 sensor
    """
    def __init__(
            self, pins=DEFAULT_SERIAL_PINS, baud=DEFAULT_BAUD_RATE,
            serial_timeout=DEFAULT_SERIAL_TIMEOUT,
            read_timeout=DEFAULT_READ_TIMEOUT,
            log_level=DEFAULT_LOGGING_LEVEL,
            id=DEFAULT_ID,
            auto_start=True, retries=DEFAULT_RETRY_COUNT):
        """
            Setup the interface for the sensor
        """

        self.logger = logging.getLogger("SPS030 Interface")
        logging.basicConfig()
        # logging.basicConfig(
        #     format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        self.logger.setLevel(log_level)
        self.id = id
        self.pins = pins
        self.logger.info("Serial pins: %s", self.pins)
        self.baud = baud
        self.logger.info("Baud rate: %s", self.baud)
        self.serial_timeout = serial_timeout
        self.logger.info("Serial Timeout: %s", self.serial_timeout)
        self.read_timeout = read_timeout
        self.logger.info("Read Timeout: %s", self.read_timeout)
        self.retries = retries
        self.logger.info("Retries: %d", self.retries)
        self.measurement_running = False
        self.timer = Timer.Chrono()
        try:
            self.serial = UART(
                self.id,
                baudrate=self.baud,
                pins=self.pins,
                timeout_chars=self.serial_timeout)
            self.logger.debug("Port Opened Successfully")
        except Exception as exp:
            self.logger.error(str(exp))
            raise SensirionException(str(exp))
        self.reset()
        if auto_start:
            self.start_measurement()

    def set_log_level(self, log_level):
        """
            Enables the class logging level to be changed after it's created
        """
        self.logger.setLevel(log_level)

    def _verify(self, recv):
        """
            Uses the last 2 bytes of the data packet from the Honeywell sensor
            to verify that the data recived is correct
        """
        calc = self._calculate_checksum(
            bytes([recv[1]]) +  bytes([recv[2]]) + bytes([recv[3]]) + bytes([recv[4]]),
            recv[5:-2])
        self.logger.debug(type(calc))
        sent = recv[-2]
        self.logger.debug(type(bytes([sent])))
        if bytes([sent]) != calc:
            self.logger.error("Checksum failure 0x%02x != 0x%02x", sent, calc)
            raise SensirionException("Checksum failure")

    def start_measurement(self):
        """
            Send the command to start the sensor reading data
        """
        self._tx(
            CMD_ADDR, CMD_START_MEASUREMENT,
            SUBCMD_START_MEASUREMENT_1 + SUBCMD_START_MEASUREMENT_2)
        time.sleep(RX_DELAY_S)
        self._rx(
            CMD_ADDR, CMD_START_MEASUREMENT)
        self.measurement_running = True
        self.timer.reset()
        self.timer.start()

    def stop_measurement(self):
        """
            Send the command to stop the sensor reading data
        """
        self._tx(CMD_ADDR, CMD_STOP_MEASUREMENT)
        time.sleep(RX_DELAY_S)
        self._rx(CMD_ADDR, CMD_STOP_MEASUREMENT)
        self.measurement_running = False

    def reset(self):
        """
            Send the reset command to the device
        """
        self._tx(CMD_ADDR, CMD_RESET)
        time.sleep(RX_DELAY_S)
        self._rx(CMD_ADDR, CMD_RESET)
        self.measurement_running = False

    def start_fan_clean(self):
        """
            Start a manual clean of the fan, takes 10s
        """
        self._tx(CMD_ADDR, CMD_START_FAN_CLEANING)
        time.sleep(RX_DELAY_S)
        self._rx(CMD_ADDR, CMD_START_FAN_CLEANING)

    def _rx(self, addr, cmd):
        """
            Recieve and process a message from the sensor
        """
        recv = b''
        chrono = Timer.Chrono()
        chrono.reset()  # Reset the timer
        chrono.start()  # Start timer
        while chrono.read() < self.read_timeout:
            inp = self.serial.read(1) # Read a character from the input
            if inp == MSG_START_STOP: # check it matches
                recv += inp # if it does add it to recieve string
                self.logger.debug(
                    "Message : 0x%02x --------", int.from_bytes(recv, "big"))
                inp = self.serial.read(1) # read the next character
                self.logger.debug("Addr byte 0x%02x", ord(inp))
                if inp == addr:
                    recv += inp
                    self.logger.debug(
                        "Message : 0x%02x --------", int.from_bytes(recv, "big"))
                    inp = self.serial.read(1)
                    self.logger.debug("Cmd byte : 0x%02x --------", ord(inp))
                    if inp == cmd:
                        recv += inp
                        self.logger.debug(
                            "Message : 0x%02x --------", int.from_bytes(recv, "big"))
                        inp = self.serial.read(1)
                        self.logger.debug("Error state byte : 0x%02x --------", ord(inp))
                        if inp != ERROR_CODE_NO_ERROR:
                            self.logger.error("State error : 0x%02x --------", ord(inp))
                            error_str = lookup_error_code(inp)
                            self.logger.error(error_str)
                            while inp != MSG_START_STOP: #empty the cache of the sensor
                                inp = self.serial.read(1)
                            raise SensirionException(error_str)
                        else:
                            recv += inp
                            self.logger.debug(
                                "Message : 0x%02x --------",
                                int.from_bytes(recv, "big"))
                            inp = self.serial.read(1)
                            while inp != MSG_START_STOP: #read remaining data until the end byte
                                recv += inp
                                self.logger.debug(
                                    "Message : 0x%02x --------",
                                    int.from_bytes(recv, "big"))
                                inp = self.serial.read(1)
                                self.logger.debug("Bytes : 0x%02x --------", ord(inp))
                            recv += inp
                            self.logger.debug(
                                "Message received : 0x%02x --------",
                                int.from_bytes(recv, "big"))

                            return recv
                    else:
                        self.logger.error(
                            "Wrong command received 0x%02x, was expecting 0x%02x",
                            ord(inp), ord(cmd))
                        self.logger.debug(
                            "Message received 0x%02x", int.from_bytes(recv, "big"))
                        raise SensirionException("Wrong command")
                else:
                    self.logger.error(
                        "Wrong address received 0x%02x, was expecting 0x%02x",
                        ord(inp), ord(addr))
                    self.logger.debug(
                        "Message received 0x%02x",
                        int.from_bytes(recv, "big"))
                    raise SensirionException("Wrong address")

        raise SensirionException("Message incomplete")

    def get_product_name(self):
        """
            Get the product name string
            In the docs this decodes to "Hello World!"
        """
        return self._device_info(SUBCMD_DEVICE_NAME).decode().rstrip('\0')

    def get_article_code(self):
        """
            Get the article Code
            In the docs this decodes to "x-xxxxxx-xx"
        """
        return self._device_info(SUBCMD_ARTICLE_CODE).decode().rstrip('\0')

    def get_serial_no(self):
        """
            Get the serial number
            In the docs this decodes to "00000000000000000000"
        """
        return self._device_info(SUBCMD_SERIAL_NO).decode().rstrip('\0')

    def _device_info(self, subcmd):
        """
            Get information from the device
        """
        self._tx(CMD_ADDR, CMD_DEVICE_INFORMATION, subcmd)
        time.sleep(RX_DELAY_S)
        return self._rx(CMD_ADDR, CMD_DEVICE_INFORMATION, subcmd)[5:-2]

    def _check_length(self, data):
        """
            Verify that the length of the data unstuffed
            corresponds to the length sent by the sensor
        """
        data_length = data[4]
        if data_length == len(data[5:-2]):
            return True
        else:
            self.logger.error(
                "Wrong data length %d, was expecting %d", len(data[5:-2]), data_length)
            raise SensirionException("Wrong data length")

    def read(self):
        """
            Wrapper for read_measurement to make it consistent with the other drivers
        """
        return self.read_measurement()

    def read_measurement(self):
        """
            Read a measurement from the device
        """
        if not self.measurement_running:
            self.logger.warning("Measurement not running, starting measurement")
            self.start_measurement()
            time.sleep(RETRY_SLEEP)
        time_diff = self.timer.read()
        if time_diff < MIN_SAMPLE_INTERVAL:
            self.logger.warning("Trying to read too frequently - forcing delay")
            time.sleep(MIN_SAMPLE_INTERVAL - time_diff)
            self.logger.debug("Sleep complete, now reading")
        count = 1
        while count <= self.retries:
            try:
                self._tx(CMD_ADDR, CMD_READ_MEASUREMENT)
                time.sleep(RX_DELAY_S)
                recv = self._rx(CMD_ADDR, CMD_READ_MEASUREMENT)
                recv_unstuffed = self._unstuff_bytes(recv)
                self._check_length(recv_unstuffed)
                self._verify(recv_unstuffed) # verify the checksum
                self.logger.debug(
                    "Verified message : 0x%02x --------",
                    int.from_bytes(recv_unstuffed, "big"))
                self.logger.debug(type(recv_unstuffed))
                self.timer.reset()
                self.timer.start()
                return SensirionReading(recv_unstuffed)
            except SensirionException as exp:
                self.logger.warning("Attempt %d/%d failed", count, self.retries)
                self.logger.error(str(exp))
                if count == self.retries:
                    raise exp
                count += 1 # increment counter
                time.sleep(RETRY_SLEEP)

    def read_cleaning_interval(self):
        """
            Read the cleaning interval from the sensor
        """
        self._tx(CMD_ADDR, CMD_READ_WRITE_AUTOCLEAN_INTERVAL, SUBCMD_READ_INTERVAL)
        time.sleep(RX_DELAY_S)
        return int.from_bytes(
            self._rx(CMD_ADDR, CMD_READ_WRITE_AUTOCLEAN_INTERVAL)[5:-2], 'big')

    def write_cleaning_interval(self, interval):
        """
            Sets the interval at which the fan should be cleaned
            set to 0 to disable automatic cleaning
        """
        if interval == 0:
            self.logger.warning("Disabling cleaning interval")
        if interval > 0xFFFFFFFF:
            self.logger.error("0x%x too large", interval)
            raise SensirionException("Interval too large")
        interval_bytes = int.to_bytes(interval, length=4, byteorder="big")
        self._tx(
            CMD_ADDR,
            CMD_READ_WRITE_AUTOCLEAN_INTERVAL,
            SUBCMD_READ_INTERVAL + interval_bytes)
        time.sleep(RX_DELAY_S)
        self._rx(
            CMD_ADDR,
            CMD_READ_WRITE_AUTOCLEAN_INTERVAL,
            SUBCMD_READ_INTERVAL)


    def _tx(self, addr, cmd, data=b''):
        """
            Build the message to send to the sensor.
            addr = b'\x01'
            cmd = b'\x01'
            data = [b'\x01',b\'x08',b'\xae', ....]
        """
        checksum = self._calculate_checksum(
            addr + cmd + bytes([len(data)]), data) #checksum calculated before byte_stuffing
        message = MSG_START_STOP
        message += self._stuff_bytes(addr)
        message += self._stuff_bytes(cmd)
        message += self._stuff_bytes(bytes([len(data)])) # Length
        message += self._stuff_bytes(data)
        message += self._stuff_bytes(checksum)
        message += MSG_START_STOP
        self.logger.debug("Message sent: 0x%02x --------", int.from_bytes(message, "big"))
        return self.serial.write(message)

    def _stuff_bytes(self, data):
        """
            Covert the data into the stuffed format required for transmission
        """
        data_stuffed = b''
        data_len = 0
        for i in data:
            self.logger.debug("Bytes : 0x%02x --------", i)
            if bytes([i]) == b'\x7E':
                data_stuffed += b'\x7D' + b'\x5E'
                data_len += 2
            elif bytes([i]) == b'\x7D':
                data_stuffed += b'\x7D' + b'\x5D'
                data_len += 2
            elif bytes([i]) == b'\x11':
                data_stuffed += b'\x7D' + b'\x31'
                data_len += 2
            elif bytes([i]) == b'\x13':
                data_stuffed += b'\x7D' + b'\x33'
                data_len += 2
            else:
                data_stuffed += bytes([i])
                data_len += 1
        return data_stuffed

    def _unstuff_bytes(self, data):
        """
        Reverse the data stuffing used on the serial protocol
        """
        data_unstuffed = b''
        i = 0
        while i < len(data):
            self.logger.debug("Lenght : %02x --------", len(data))
            self.logger.debug("i : %02x --------", i)
            self.logger.debug("Bytes : 0x%02x --------", data[i])
            if bytes([data[i]]) == b'\x7d':
                self.logger.debug("Bytes +1 : 0x%02x --------", data[i+1])
                if bytes([data[i + 1]]) == b'\x5e':
                    data_unstuffed += b'\x7e'
                    i += 2
                elif bytes([data[i + 1]]) == b'\x5d':
                    data_unstuffed += b'\x7d'
                    i += 2
                elif bytes([data[i + 1]]) == b'\x31':
                    data_unstuffed += b'\x11'
                    i += 2
                elif bytes([data[i + 1]]) == b'\x33':
                    data_unstuffed += b'\x13'
                    i += 2
            else:
                data_unstuffed += bytes([data[i]])
                i += 1
        self.logger.debug(
            "Message unstuffed: 0x%02x --------",
            int.from_bytes(data_unstuffed, "big"))
        return data_unstuffed


    def _calculate_checksum(self, header, data):
        """
            Sum all the bytes between MSG_START_STOP (included) and the Checksum
        """
        self.logger.debug("Type header : %s", type(header))
        self.logger.debug("Type data : %s", type(data))
        sum_bytes = bytes([(sum(data) + sum(header))%256])
        # Take the LSB
        lsb = (ord(sum_bytes) >> 0)
        # Invert it to get the checksum
        self.logger.debug("Checksum : 0x%02x", ord(bytes([255 - lsb])))
        return bytes([255 - lsb])
