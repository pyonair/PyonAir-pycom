#!/usr/bin/env python
from plantower import Plantower, PlantowerException
import time
from sd_card import SDCard
from machine import RTC
from strings import sensor_logfile_template, timestamp_template
from machine import Timer

# Setting
loop_time = 0.1  # delay between the sensor readings (seconds)

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: get time from GPS
now = rtc.now()

# Initialise SD card
sensor_logfile = sensor_logfile_template.format(*now)
status_logfile = 'status_log.txt'
sd = SDCard(
    rtc=rtc,
    sensor_logfile=sensor_logfile,
    status_logfile=status_logfile,
    debug=True
)

plantower = Plantower()

# Chronometer for timing the loop execution
chrono = Timer.Chrono()
chrono.start()
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
        # TODO: log exception
    finally:
        elapsed = chrono.read()
        if elapsed < loop_time:
            time.sleep(loop_time - elapsed)
        # TODO: raise warning if the elapsed time is loner than the loop_time
        chrono.reset()

# TODO: take mean of the messages if two or more readings per second
