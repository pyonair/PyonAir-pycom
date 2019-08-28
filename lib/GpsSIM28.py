from machine import UART, Timer, Pin
from micropyGPS import MicropyGPS
from RtcDS1307 import clock
from Configuration import config
from SensorLogger import SensorLogger
from helper import minutes_from_midnight
import strings as s
import time
import pycom
import uos

# Initialize GPS power circuitry
GPS_transistor = Pin('P19', mode=Pin.OUT)
GPS_transistor.value(0)

# gps library to parse, interpret and store data coming from the serial
gps = MicropyGPS()

# Create GPS sensor logger
GPS_logger = SensorLogger(sensor_name=s.GPS, terminal_out=True)


# delete serial used for terminal out and initialize serial for GPS
def gps_init(logger):

    logger.info("Turning GPS on - Terminal output is disabled until GPS finishes")
    uos.dupterm(None)  # deinit terminal output on serial bus 0

    # turn GPS module on via transistor
    GPS_transistor.value(1)

    # set up serial input for gps signals
    serial = UART(0, baudrate=9600, pins=('P22', 'P21'))  # Tx, Rx

    chrono = Timer.Chrono()
    chrono.start()

    return serial, chrono


# delete serial used for GPS and re-initialize terminal out
def gps_deinit(serial, logger, message):

    # turn off GPS via turning off transistor
    GPS_transistor.value(0)

    # de-initialize GPS serial
    serial.deinit()

    # re-initialize terminal out
    terminal = UART(0, 115200)
    uos.dupterm(terminal)

    # print any important messages concerning the gps
    if message is not False:
        logger.info(message)
    logger.info("Turning GPS off - Terminal output enabled")


def get_time(rtc, led, logger):

    logger.info("Getting UTC datetime via GPS")
    serial, chrono = gps_init(logger)  # initialize serial and timer
    message = False  # no message while terminal is disabled (by default)
    com_counter = int(chrono.read())  # counter for checking whether gps is connected
    if led:  # led indicator enabled - when get_time is blocking upon boot
        led_counter = int(chrono.read())  # counter for blinking led

    while True:
        # data_in = '$GPRMC,085258.000,A,5056.1384,N,00123.1522,W,0.00,159.12,200819,,,A*7E\r\n'
        data_in = (str(serial.readline()))[1:]

        if (int(chrono.read()) - com_counter) >= 10:
            gps_deinit(serial, logger, message)
            raise Exception("GPS enabled, but not connected")

        for char in data_in:
            sentence = gps.update(char)
            if sentence == "GPRMC":
                com_counter = int(chrono.read())
                if gps.valid:

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

                    # Turn flashing blue led indicator off if enabled, and exit function or thread
                    if led:
                        pycom.rgbled(0x552000)  # flash orange to indicate continuation of startup
                    gps_deinit(serial, logger, message)
                    return

        # If function is blocking, led should be set - blinking blue light indicating that program is waiting for
        # gps to acquire current utc time before continuing execution
        if led:
            if int(chrono.read()) > led_counter:
                led_counter = int(chrono.read())
                if led_counter % 2 == 0:
                    pycom.rgbled(0x000077)
                else:
                    pycom.rgbled(0x000000)

        # If timeout elapsed exit function or thread
        # if chrono.read() >= config.get_config("GPS_timeout"):
        if chrono.read() >= 10:
            gps_deinit(serial, logger, message)
            raise Exception("GPS timeout")


def get_position(logger):
    serial, chrono = gps_init(logger)

    message = False
    com_counter = int(chrono.read())

    while True:
        data_in = '$GPGGA,085259.000,5056.1384,N,00123.1522,W,1,8,1.17,25.1,M,47.6,M,,*7D\r\n'
        # data_in = (str(serial.readline()))[1:]

        if (int(chrono.read()) - com_counter) >= 10:
            gps_deinit(serial, logger, message)
            raise Exception("GPS enabled, but not connected")

        for char in data_in:
            sentence = gps.update(char)
            if sentence == "GPGGA":
                com_counter = int(chrono.read())

                if 0 < gps.hdop < 5 and gps.satellites_in_use >= 3:

                    message = """Successfully acquired location from GPS
                    Longitude: {}
                    Latitude: {}
                    Altitude: {}""".format(gps.longitude, gps.latitude, gps.altitude)

                    # Log GPS location
                    timestamp = s.csv_timestamp_template.format(*time.gmtime())  # get current time in desired format
                    lst_to_log = [timestamp] + gps.latitude + gps.longitude + gps.altitude
                    line_to_log = ','.join(lst_to_log)
                    GPS_logger.log_row(line_to_log)

                    # Construct LoRa message
                    line_to_send = str(minutes_from_midnight()) + ',' + str(config.get_config("GPS_id")) + ',' + \
                                     ','.join(lst_to_log[1:]) + '\n'

                    # Append lines to sensor_name.csv.tosend
                    lora_filepath = s.lora_path + s.GPS_lora_file
                    with open(lora_filepath, 'w') as f_tosend:
                        f_tosend.write(line_to_send)

        # If timeout elapsed exit function or thread
        if chrono.read() >= config.get_config("GPS_timeout"):
            gps_deinit(serial, logger, message)
            raise Exception("GPS timeout")

