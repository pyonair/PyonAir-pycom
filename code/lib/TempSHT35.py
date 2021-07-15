from machine import I2C, Timer

from Configuration import Configuration 
from helper import blink_led
#from strings import csv_timestamp_template
from Constants import TIME_ISO8601_FMT
import time


# Temp Res: 0.01C, Temp Acc: +/-0.1C, Humid Res: 0.01%, Humid Acc: +/-1.5%
class TempSHT35(object):

    def __init__(self, config, logger, status_logger):
        self.config =config
        self.logger = logger
        self.status_logger = status_logger

        # Initialise i2c - bus no., type, baudrate, i2c pins
        self.i2c = I2C(0, I2C.MASTER, baudrate=9600, pins=('P9', 'P10'))
        self.address = 0x45

        # get one sensor reading upon init to catch any errors and calibrate the sensor
        self.read()
        # start a periodic timer interrupt to poll readings at a frequency
        self.processing_alarm = Timer.Alarm(self.process_readings, s=int(self.config.get_config("TEMP_period")), periodic=True)

    def read(self):
        # high repeatability, clock stretching disabled
        self.i2c.writeto_mem(self.address, 0x24, 0x00)

        # measurement duration < 16 ms
        time.sleep(0.016)

        # read 6 bytes back
        # Temp MSB, Temp LSB, Temp CRC, Humidity MSB, Humidity LSB, Humidity CRC
        data = self.i2c.readfrom_mem(self.address, 0x00, 6)
        temperature = data[0] * 256 + data[1]
        celsius = -45 + (175 * temperature / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
        if data[2] != CRC(data[:2]):
            raise RuntimeError("temperature CRC mismatch")
        if data[5] != CRC(data[3:5]):
            raise RuntimeError("humidity CRC mismatch")
        return [celsius, humidity]

    def process_readings(self, arg):
        """
        Processes readings form the temperature sensor and logs it to the terminal and the SD card.
        Takes a dummy argument required by the timed interrupt callback.
        """
        # read and log pm sensor data
        try:
            timestamp = TIME_ISO8601_FMT.format(*time.gmtime())  # get current time in desired format
            read_lst = self.read()  # read SHT35 sensor - [celsius, humidity] to ~5 significant figures
            round_lst = [int(round(x, 1)*10) for x in read_lst]  # round readings to 1 significant figure, shift left, cast to int
            str_round_lst = list(map(str, round_lst))  # cast int to string
            lst_to_log = [timestamp] + str_round_lst
            line_to_log = ','.join(lst_to_log)
            self.logger.log_row(line_to_log)
        except Exception as e:
            self.status_logger.exception("Failed to read from temperature and humidity sensor")
            blink_led((0x550000, 0.4, True))


#  Cycling redundancy check
def CRC(data):
    crc = 0xff
    for s in data:
        crc ^= s
        for i in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc
