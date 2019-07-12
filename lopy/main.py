#!/usr/bin/env python

from machine import RTC, Timer, SD, Pin
from PM_thread import pm_thread
from ButtonPress import ButtonPress
import _thread
import os
from LoggerFactory import LoggerFactory
from SensorLogger import SensorLogger
from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
from configuration import read_configuration
from EventScheduler import EventScheduler

# Provisional globals
path = '/sd/'
sensor_name = 'PM1'
PM1_processing = path + sensor_name + '.csv.processing'
interval_m = 15  # default interval for averages (minutes)

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: if RTC has no time, set RTC time via Wifi and/or GPS
now = rtc.now()

# Mount SD card
sd = SD()
os.mount(sd, '/sd')

# Initialise LoggerFactory and loggers
logger_factory = LoggerFactory()
status_logger = logger_factory.create_status_logger('status_logger', level=DEBUG, filename='status_log.txt')
status_logger.info('booted now')
sensor_logger = SensorLogger(filename=path + sensor_name + '.csv.current', terminal_out=True)

# Delete 'PM1.csv.processing' if it exists TODO: send the content over LoRa instead
if PM1_processing in os.listdir():
    status_logger.info(PM1_processing + 'already exists, removing it')
    os.remove(PM1_processing)

# Read configuration file to get preferences
interval_m = read_configuration(logger=status_logger)['interval']

# Start 1st PM sensor thread with id: PM1
_thread.start_new_thread(pm_thread, (sensor_name, sensor_logger, status_logger))

# Start calculating averages and sending data over LoRa
PM1_Events = EventScheduler(interval_m, rtc, logger=status_logger, sensor_name=sensor_name)

# Initialise interrupt on user button for configuration over wifi
user_button = ButtonPress(logger=status_logger)
pin_14 = Pin("P14", mode=Pin.IN, pull=None)
pin_14.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, user_button.press_handler)
