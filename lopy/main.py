#!/usr/bin/env python
from plantower import Plantower, PlantowerException
import time
from sd_card import SDCard
from machine import RTC
from strings import sensor_logfile_template, timestamp_template

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: get time from GPS
now = rtc.now()

# Initialise SD card
sensor_logfile = sensor_logfile_template.format(*now)
status_logfile = 'status_log.txt'
sd = SDCard(
    sensor_logfile=sensor_logfile,
    status_logfile=status_logfile
)

# Create log file with headers
sd.create_sensor_log_file(sensor_logfile)

plantower = Plantower()

while (True):
    try:
        recv = plantower.read()
        if recv:
            print(recv)
            print()
            sd.log_sensor_line(str(recv))
    except PlantowerException as e:
        status_line = ', '.join([timestamp_template.format(*rtc.now()), str(e.__class__)])
        print(status_line)
        sd.log_sensor_line(status_line)
    time.sleep(0.1)
