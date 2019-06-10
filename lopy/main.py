#!/usr/bin/env python
from plantower import Plantower, PlantowerException
import time
from sd_card import SDCard
from machine import RTC
from strings import log_file_template, timestamp_template

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0)) # TODO: get time from GPS

# Initialise SD card
sd = SDCard()

# Create log file with headers
now = rtc.now()
log_file = '{}.csv'.format(log_file_template.format(*now))
sd.create_log_file(log_file)

plantower = Plantower()

while (True):
    try:
        recv = plantower.read()
        if recv:
            print(recv)
            print()
            sd.write_line(log_file, str(recv))
    except PlantowerException as e:
        error_line = ', '.join([timestamp_template.format(*rtc.now()), str(e.__class__)])
        print(error_line)
        sd.write_line('error_log.txt', error_line)
    time.sleep(0.1)
