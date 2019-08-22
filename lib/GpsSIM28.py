from machine import UART, Timer
from micropyGPS import MicropyGPS
from RtcDS1307 import clock
from Configuration import config
import pycom
import uos

# gps library to parse, interpret and store data coming from the serial
gps = MicropyGPS()


def get_time(rtc, led, logger, GPS_transistor):

    logger.info("Getting UTC datetime via GPS")
    logger.info("Turning GPS on - Terminal output is disabled until GPS finishes")
    message = False

    # turn GPS module on via transistor
    GPS_transistor.value(1)
    # set up serial input for gps signals
    serial = UART(0, baudrate=9600, pins=('P22', 'P21'))  # Tx, Rx

    timeout = config.get_config("GPS_timeout")
    chrono = Timer.Chrono()
    chrono.start()
    com_counter = int(chrono.read())
    if led:
        led_counter = int(chrono.read())

    while True:
        # data_in = '$GPRMC,085258.000,A,5056.1384,N,00123.1522,W,0.00,159.12,200819,,,A*7E\r\n'
        data_in = (str(serial.readline()))[1:]

        if (int(chrono.read())-com_counter) >= 10:
            gps_deinit(serial, logger, message, GPS_transistor)
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
                    h_day, h_mnth, h_yr = int(str(gps.date[0]), 16), int(str(gps.date[1]), 16), int(str(gps.date[2]), 16)
                    h_hr, h_min, h_sec = int(str(gps.timestamp[0]), 16), int(str(gps.timestamp[1]), 16), int(str(int(gps.timestamp[2])), 16)
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
                    gps_deinit(serial, logger, message, GPS_transistor)
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
        if chrono.read() >= timeout:
            gps_deinit(serial, logger, message, GPS_transistor)
            raise Exception("GPS timeout")


# delete serial used for GPS and re-initialize terminal out
def gps_deinit(serial, logger, message, GPS_transistor):

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


# ToDo: test time first, then finish coding position
# def get_position():
#     while True:
#
#         # input = '$GPGGA,085259.000,5056.1384,N,00123.1522,W,1,8,1.17,25.1,M,47.6,M,,*7D\r\n'
#
#
#         if sentence == "GPGGA":
#             print('Parsed a', sentence, 'Sentence')
#             print('Parsed Strings', gps.gps_segments)
#             print('Sentence CRC Value:', hex(gps.crc_xor))
#             print('Longitude', gps.longitude)
#             print('Latitude', gps.latitude)
#             print('UTC Timestamp:', gps.timestamp)
#             print('Fix Status:', gps.fix_stat)
#             print('Altitude:', gps.altitude)
#             print('Height Above Geoid:', gps.geoid_height)
#             print('Horizontal Dilution of Precision:', gps.hdop)
#             print('Satellites in Use by Receiver:', gps.satellites_in_use)
#             #  device moved?
#             #  dilution of precision is great?
#             # satellites used at least 3?
#             # send lat and long
#
#         # write a checker that checks if we have got both sentences
#         # write a timer that stops trying until next interval if timeout reached
