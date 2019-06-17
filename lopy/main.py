#!/usr/bin/env python
from plantower import Plantower, PlantowerException
import time
from sd_card import SDCard
from machine import RTC
from strings import log_file_template, timestamp_template

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: get time from GPS
now = rtc.now()

# Initialise SD card
logfile = '{}.csv'.format(log_file_template.format(*now))
error_logfile = 'error_log.txt'
sd = SDCard(
    logfile=logfile,
    error_logfile=error_logfile
)

# Create log file with headers
sd.create_log_file(logfile)

plantower = Plantower()

while (True):
    try:
        recv = plantower.read()
        if recv:
            print(recv)
            print()
            sd.log_line(str(recv))
    except PlantowerException as e:
        error_line = ', '.join([timestamp_template.format(*rtc.now()), str(e.__class__)])
        print(error_line)
        sd.log_line(error_line)
    time.sleep(0.1)
