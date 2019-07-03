#!/usr/bin/env python

from sd_card import SDCard
from machine import RTC, Timer
from strings import sensor_logfile_template
from PM_thread import pm_thread
import _thread
import time

# Setting
loop_time = 0.1  # delay between the sensor readings (seconds)

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: get time from GPS
now = rtc.now()

# Initialise SD card
sd = SDCard(
    rtc=rtc,
    sensor_logfile=sensor_logfile_template.format(*now),
    status_logfile='status_log.txt',
    debug=True
)

# Start 1st PM sensor thread with id: PM1
_thread.start_new_thread(pm_thread, (sd, 'PM1'))

while True:
    print("Main thread executing")
    time.sleep(1)
