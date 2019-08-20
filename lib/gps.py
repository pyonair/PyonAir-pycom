from machine import UART
from micropyGPS import MicropyGPS
from RtcDS1307 import clock
import _thread
import time

# set up serial input for gps signals
serial = UART(2, baudrate=9600, pins=('P22', 'P21'))  # Tx, Rx

# gps library to parse, interpret and store data coming from the serial
gps = MicropyGPS()


def get_time(blocking=False, rtc=None):

    if blocking:
        parse_time(rtc)
    else:
        _thread.start_new_thread(parse_time, rtc)


#ToDo: Add timeout
def parse_time(rtc):
    while True:
        data_in = '$GPRMC,085258.000,A,5056.1384,N,00123.1522,W,0.00,159.12,200819,,,A*7E\r\n'
        # data_in = (str(serial.readline()))[1:]

        for char in data_in:
            sentence = gps.update(char)
            if sentence == "GPRMC":

                print('UTC Timestamp:', gps.timestamp)
                print('Date Stamp:', gps.date)
                print('Data is Valid:', gps.valid)

                if gps.valid:

                    # Set current time on pycom
                    datetime = (int('20' + str(gps.date[2])), gps.date[1], gps.date[0], gps.timestamp[0],
                                gps.timestamp[1], gps.timestamp[2], 0, 0)
                    rtc.init(datetime)

                    # Set current time on RTC module if connected
                    h_day, h_mnth, h_yr = int(gps.date[0], 16), int(gps.date[1], 16), int(gps.date[2], 16)
                    h_hr, h_min, h_sec = int(gps.timestamp[0], 16), int(gps.timestamp[1], 16), int(gps.timestamp[2], 16)
                    try:
                        clock.set_time(h_yr, h_mnth, h_day, h_hr, h_min, h_sec)
                    except Exception:
                        pass

                    return



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
