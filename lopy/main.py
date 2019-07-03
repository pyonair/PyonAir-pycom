#!/usr/bin/env python

from sd_card import SDCard
from machine import RTC, Timer
from strings import sensor_logfile_template
from PM_thread import pm_thread
from interrupt import ButtonPress
from machine import Pin
import _thread
import time


# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: if RTC has no time, set RTC time via Wifi and/or GPS
now = rtc.now()

# Initialise SD card
sd = SDCard(
    rtc=rtc,
    sensor_logfile=sensor_logfile_template.format(*now),
    status_logfile='status_log.txt',
    debug=True
)

# TODO: Initialise Logger

# initialise interrupt for configuration over wifi
interrupt = ButtonPress(sd)
p = Pin("P14", mode=Pin.IN, pull=None)
p.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, interrupt.press_handler)

# Read configuration file
sd.get_config()

# TODO: Process and send remaining data from previous boot

# Start 1st PM sensor thread with id: PM1
_thread.start_new_thread(pm_thread, (sd, 'PM1'))

while True:
    pass
    # print("Main thread executing")
    # time.sleep(3)
