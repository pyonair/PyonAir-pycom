from machine import UART, Timer, Pin
from micropyGPS import MicropyGPS
from RtcDS1307 import clock
from Configuration import Configuration #import config
from helper import secOfTheMonth , blink_led
#import strings as s
import time
import uos
import sys
import _thread
from Constants import TIME_ISO8601_FMT


#good for thread
#take rtc and update time if get fix
def SetRTCtime(rtc,config, logger):
    gps = GPSSIM28(config, logger)
    gps.get_time(rtc)

def logGPS(rtc,config, logger):
    logger.info("Not implemented")
    #gps = GPSSIM28(config, logger)
    #gps.get_position(rtc)
    #TODO: not implemented

class GPSSIM28:

    def __init__(self,config, logger):
        self.logger= logger
        self.config = config # Configuration(logger) #TODO: Temp fix to get values in here -- but change to static
        # Initialise GPS power circuitry
        self.GPS_transistor = Pin('P19', mode=Pin.OUT)
        self.GPS_transistor.value(0)

        # gps library to parse, interpret and store data coming from the serial
        self.gps = MicropyGPS()

        # Having a lock is necessary, because it is possible to have two gps threads running at the same time
        self.gps_lock = _thread.allocate_lock()


    # delete serial used for terminal out and initialise serial for GPS
    def gps_init(self):
        """
        De-initialises terminal output, and opens serial for the GPS
        :param logger: status logger
        :type logger: LoggerFactory object
        :return: serial, chrono, inidcator_led
        :rtype: UART object, Chrono object, Alarm object
        """

        self.logger.info("Turning GPS on - Terminal output is disabled until GPS finishes")

        uos.dupterm(None)  # deinit terminal output on serial bus 0

        # turn GPS module on via transistor
        GPS_transistor.value(1)

        # set up serial input for gps signals
        serial = UART(0, baudrate=9600, pins=('P22', 'P21'))  # Tx, Rx

        chrono = Timer.Chrono()
        chrono.start()

        indicator_led = Timer.Alarm(blink_led, s=1.6, arg=(0x000055, 0.4, False), periodic=True)

        return serial, chrono, indicator_led


    # delete serial used for GPS and re-initialise terminal out
    def gps_deinit(self,serial, message, indicator_led):
        """
        De-initialises GPS serial bus, initialises terminal output and prints message to the terminal
        :param serial: GPS serial bus
        :type serial: UART object
        :param logger: status logger
        :type logger: LoggerFactory object
        :param message: message to display after terminal output was enabled
        :type message: str
        :param indicator_led: Timer for led indicator
        :type indicator_led: Timer object
        """

        # turn off GPS via turning off transistor
        GPS_transistor.value(0)

        # de-initialise GPS serial
        serial.deinit()

        # re-initialise terminal out
        terminal = UART(0, 115200)
        uos.dupterm(terminal)

        indicator_led.cancel()

        # print any important messages concerning the gps
        if message is not False:
            self.logger.info(message)
        self.logger.info("Turning GPS off - Terminal output enabled")


    def get_time(self,rtc):
        """
        Acquires UTC date time from the GPS
        :param rtc: pycom real time clock
        :type rtc: RTC object
        :param logger: status logger
        :type logger: LoggerFactory object
        :return: True of False
        :rtype: bool
        """

        if self.gps_lock.locked():
            self.logger.debug("Waiting for other gps thread to finish")
        with self.gps_lock:
            self.logger.info("Getting UTC datetime via GPS")

            serial, chrono, indicator_led = self.gps_init()  # initialise serial and timer
            com_counter = int(chrono.read())  # counter for checking whether gps is connected
            timeout = int(float(self.config.get_config("GPS_timeout")) * 60)
            message = False  # no message while terminal is disabled (by default)

            while True:
                # data_in = '$GPRMC,085258.000,A,5056.1384,N,00123.1522,W,0.00,159.12,200819,,,A*7E\r\n'
                data_in = (str(serial.readline()))[1:]

                if (int(chrono.read()) - com_counter) >= 10:
                    self.gps_deinit(serial, logger, message, indicator_led)
                    self.logger.error("GPS enabled, but not connected")
                    return False

                if data_in[1:4] != "$GP":
                    time.sleep(1)
                else:
                    for char in data_in:
                        sentence = self.gps.update(char)
                        if sentence == "GPRMC":
                            com_counter = int(chrono.read())
                            if self.gps.valid:

                                # Set current time on pycom - convert seconds (timestamp[2]) from float to int
                                datetime = (int('20' + str(gps.date[2])), gps.date[1], gps.date[0], gps.timestamp[0],
                                            gps.timestamp[1], int(gps.timestamp[2]), 0, 0)
                                rtc.init(datetime)

                                # Set current time on RTC module if connected - convert seconds (timestamp[2]) from float to int
                                h_day, h_mnth, h_yr = int(str(gps.date[0]), 16), int(str(gps.date[1]), 16), int(str(gps.date[2]),
                                                                                                                16)
                                h_hr, h_min, h_sec = int(str(gps.timestamp[0]), 16), int(str(gps.timestamp[1]), 16), int(
                                    str(int(gps.timestamp[2])), 16)
                                try:
                                    clock.set_time(h_yr, h_mnth, h_day, h_hr, h_min, h_sec)
                                    message = """GPS UTC datetime successfully updated on pycom board
                                                GPS UTC datetime successfully updated on RTC module"""
                                except Exception:
                                    message = """GPS UTC datetime successfully updated on pycom board
                                                Failed to set GPS UTC datetime on the RTC module"""

                                self.gps_deinit(serial, logger, message, indicator_led)
                                return True

                # If timeout elapsed exit function or thread
                if chrono.read() >= timeout:
                    self.gps_deinit(serial, self.logger, message, indicator_led)
                    self.logger.error("""GPS timeout
                    Check if GPS module is connected
                    Place device under clear sky
                    Increase GPS timeout in configurations""")
                    return False


    def get_position(self): # lora):
        """
        Acquires latitude, longitude and altitude from GPS based on HDOP
        :param logger: status logger
        :type logger: LoggerFactory object
        :param lora: LoRaWAN object, False if lora is not enabled
        :type lora: LoRaWAN object
        :return: True or False
        :rtype: bool
        """

        if self.gps_lock.locked():
            self.logger.debug("Waiting for other gps thread to finish")
        with self.gps_lock:
            self.logger.info("Getting position via GPS")

            serial, chrono, indicator_led = gps_init(logger)
            com_counter = int(chrono.read())  # counter for checking whether gps is connected
            timeout = int(float(self.config.get_config("GPS_timeout")) * 60)
            message = False

            while True:
                # data_in = '$GPGGA,085259.000,5056.1384,N,00123.1522,W,1,8,1.17,25.1,M,47.6,M,,*7D\r\n'
                data_in = (str(serial.readline()))[1:]
                #TODO: be careful with read and substring -- check for []

                if (int(chrono.read()) - com_counter) >= 10:
                    gps_deinit(serial, self.logger, message, indicator_led)
                    self.logger.error("GPS enabled, but not connected")
                    return False

                if data_in[1:4] != "$GP":
                    time.sleep(1)
                else:
                    for char in data_in:
                        sentence = gps.update(char)
                        if sentence == "GPGGA":
                            com_counter = int(chrono.read())

                            # set aim for the quality of the signal based on the time elapsed
                            elapsed = chrono.read() / timeout

                            hdop_aim = [1, 1.2, 1.5, 1.8, 2, 2.5, 3, 4, 5, 6, 7]
                            time_limit = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]

                            for index in range(len(time_limit)):
                                if elapsed < time_limit[index]:
                                    break

                            # Process data only if quality of signal is great
                            if 0 < gps.hdop <= hdop_aim[index] and self.gps.satellites_in_use >= 3:

                                latitude = gps.latitude[0] + self.gps.latitude[1]/60
                                if self.gps.latitude[2] == 'S':
                                    latitude = -latitude

                                longitude = gps.longitude[0] + self.gps.longitude[1]/60
                                if self.gps.longitude[2] == 'W':
                                    longitude = -longitude

                                message = """Successfully acquired location from GPS
                                Satellites used: {}
                                HDOP: {}
                                Latitude: {}
                                Longitude: {}
                                Altitude: {}""".format(gps.satellites_in_use, gps.hdop, latitude, longitude, gps.altitude)

                                # Process GPS location
                                timestamp = TIME_ISO8601_FMT.format(*time.gmtime())  # get current time in desired format
                                lst_to_log = [timestamp, latitude, longitude, self.gps.altitude]
                                str_lst_to_log = list(map(str, lst_to_log))  # cast to string
                                line_to_log = ','.join(str_lst_to_log) + '\n'

                                # Print to terminal and log to archive #TODO: why archive?
                                sys.stdout.write(s.GPS + " - " + line_to_log)
                                with open(s.archive_path + s.GPS + '.csv', 'a') as f_archive:
                                    f_archive.write(line_to_log)

                                if False: #TODO re-enable lora? lora is not False:
                                    # get year and month from timestamp
                                    year_month = timestamp[2:4] + "," + timestamp[5:7] + ','

                                    # get minutes since start of the month
                                    minutes = str(secOfTheMonth())

                                    # Construct LoRa message
                                    line_to_log = year_month + 'G,' + str(config.get_config("fmt_version")) + ',' + minutes + ',' \
                                                + str(config.get_config("GPS_id")) + ',' + ','.join(str_lst_to_log[1:]) + '\n'

                                    # Logs line_to_log to be sent over lora
                                    lora.lora_buffer.write(line_to_log)

                                self.gps_deinit(serial, self.logger, message, indicator_led)
                                return True

                # If timeout elapsed exit function or thread
                if chrono.read() >= timeout:
                    gps_deinit(serial, self.logger, message, indicator_led)
                    self.logger.error("""GPS timeout
                    Check if GPS module is connected
                    Place device under clear sky
                    Increase GPS timeout in configurations""")
                    return False
