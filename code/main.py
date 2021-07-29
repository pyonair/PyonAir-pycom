#!/usr/bin/env python
from network import WLAN
from helper import blink_led
import os
import time
import pycom
from _pybytes import Pybytes
from _pybytes_config import PybytesConfig
from machine import RTC, unique_id
from machine import SD, Pin, reset
from initialisation import initialise_time  # TODO: clunky refactor
import loggingpycom
from Constants import *

# TODO: provision if key on sd card

# set connect to false in config file?


pycom.nvs_set('pybytes_debug', 99)  # 0 warning - 99 all
Pybytes.update_config('pybytes_autostart', False,
                      permanent=True, silent=False, reconnect=False)

# pdb.set_trace()


pycom.pybytes_on_boot(False)
conf = PybytesConfig().read_config()
print("CONFIG:  ")
print(conf)
pybytes = Pybytes(conf)

# TIME
# Get current time
#rtc = RTC()
# no_time, update_time_later = initialise_time(rtc, True, status_logger) #TODO: True is use gps


pybytes.start(autoconnect=False)
pybytes.send_signal(1, 0)  # Sort of similar to uptime, sent to note reboot


# ==========================

# Disable default wifi
wlan = WLAN()
wlan.deinit()

pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange to indicate startup

# Try to mount SD card, if this fails, keep blinking red and do not proceed
try:

    #from loggingpycom import DEBUG
    from LoggerFactory import LoggerFactory
    from UserButton import UserButton
    # Initialise LoggerFactory and status logger
    logger_factory = LoggerFactory()
    status_logger = logger_factory.create_status_logger(DEFAULT_LOG_NAME, level=loggingpycom.DEBUG, terminal_out=True,
                                                        filename=LOG_FILENAME)

    # Initialise button interrupt on pin 14 for user interaction
    user_button = UserButton(status_logger)
    pin_14 = Pin("P14", mode=Pin.IN, pull=Pin.PULL_DOWN)
    pin_14.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING,
                    user_button.button_handler)

    # Mount SD card
    sd = SD()
    os.mount(sd, '/sd')

except Exception as e:
    print(str(e))
    reboot_counter = 0
    while True:
        blink_led((0x550000, 0.5, True))  # blink red LED
        time.sleep(0.5)
        reboot_counter += 1
        if reboot_counter >= 180:
            reset()

try:
    from machine import RTC, unique_id
    from initialisation import initialise_time
    from ubinascii import hexlify
    from Configuration import config
    from new_config import new_config
    from software_update import software_update
    import strings as s
    import ujson

    # Read configuration file to get preferences
    config.read_configuration()

    """SET CODE VERSION NUMBER - if new tag is added on git, update code version number accordingly"""
    # ToDo: Update OTA.py so if version is 0.0.0, it backs up all existing files, and adds all files as new.
    # ToDo: Set code_version to '0.0.0' in default config, and remove the line below
    config.save_config({"code_version": "0.2.6"})

    """SET FORMAT VERSION NUMBER - version number is used to indicate the data format used to decode LoRa messages in
    the back end. If the structure of the LoRa message is changed during update, increment the version number and
    add a corresponding decoder to the back-end."""
    config.save_config({"fmt_version": 1})

    # Override Preferences - DEVELOPER USE ONLY - keep all overwrites here
    if 'debug_config.json' in os.listdir('/flash'):
        status_logger.warning(
            "Overriding configuration with the content of debug_config.json")
        with open('/flash/debug_config.json', 'r') as f:
            config.set_config(ujson.loads(f.read()))
            status_logger.warning(
                "Configuration changed to: " + str(config.get_config()))

    # Check if GPS is enabled in configurations
    gps_on = True
    if config.get_config("GPS") == "OFF":
        gps_on = False

    # Get current time
    rtc = RTC()
    no_time, update_time_later = initialise_time(rtc, gps_on, status_logger)

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if not config.is_complete(status_logger) or config.get_config("device_id") != device_id:
        config.reset_configuration(status_logger)
        #  Force user to configure device, then reboot
        new_config(status_logger, arg=0)

    # User button will enter configurations page from this point on
    user_button.set_config_enabled(True)

    # If initialise time failed to acquire exact time, halt initialisation
    if no_time:
        raise Exception("Could not acquire UTC timestamp")

    # Check if updating was triggered over LoRa
    if config.get_config("update"):
        software_update(status_logger)

except Exception as e:
    status_logger.exception(str(e))
    reboot_counter = 0
    try:
        while user_button.get_reboot():
            blink_led((0x555500, 0.5, True))  # blink yellow LED
            time.sleep(0.5)
            reboot_counter += 1
            if reboot_counter >= 180:
                status_logger.info("rebooting...")
                reset()
        new_config(status_logger, arg=0)
    except Exception:
        reset()

pycom.rgbled(0x552000)  # flash orange until its loaded

# If sd, time, logger and configurations were set, continue with initialisation
try:
    from machine import Timer
    from SensorLogger import SensorLogger
    from EventScheduler import EventScheduler
    from helper import blink_led, get_sensors, led_lock
    from averages import get_sensor_averages
    from TempSHT35 import TempSHT35
    import GpsSIM28
    import _thread
    from initialisation import initialise_pm_sensor, initialise_file_system, remove_residual_files, get_logging_level
    from LoRaWAN import LoRaWAN

    # Configurations are entered parallel to main execution upon button press for 2.5 secs
    user_button.set_config_blocking(False)

    # Set debug level - has to be set after logger was initialised and device was configured
    logger_factory.set_level('status_logger', get_logging_level())

    # Initialise file system
    initialise_file_system()

    # Remove residual files from the previous run (removes all files in the current and processing dir)
    remove_residual_files()

    # Get a dictionary of sensors and their status
    sensors = get_sensors()

    # Join the LoRa network
    lora = False
    if (True in sensors.values() or gps_on) and config.get_config("LORA") == "ON":
        lora = LoRaWAN(status_logger)

    # Initialise temperature and humidity sensor thread with id: TEMP
    if sensors[s.TEMP]:
        TEMP_logger = SensorLogger(sensor_name=s.TEMP, terminal_out=True)
        if config.get_config(s.TEMP) == "SHT35":
            temp_sensor = TempSHT35(TEMP_logger, status_logger)
    status_logger.info("Temperature and humidity sensor initialised")

    # Initialise PM power circuitry
    PM_transistor = Pin('P20', mode=Pin.OUT)
    PM_transistor.value(0)
    if config.get_config(s.PM1) != "OFF" or config.get_config(s.PM2) != "OFF":
        PM_transistor.value(1)

    # Initialise PM sensor threads
    if sensors[s.PM1]:
        initialise_pm_sensor(sensor_name=s.PM1, pins=(
            'P3', 'P17'), serial_id=1, status_logger=status_logger)
    if sensors[s.PM2]:
        initialise_pm_sensor(sensor_name=s.PM2, pins=(
            'P11', 'P18'), serial_id=2, status_logger=status_logger)

    # Start scheduling lora messages if any of the sensors are defined
    if True in sensors.values():
        PM_Events = EventScheduler(
            logger=status_logger, data_type="sensors", lora=lora)
    if gps_on:
        GPS_Events = EventScheduler(
            logger=status_logger, data_type="gps", lora=lora)

    status_logger.info("Initialization finished")

    # Blink green three times to identify that the device has been initialised
    for val in range(3):
        blink_led((0x005500, 0.5, True))
        time.sleep(0.5)
    # Initialise custom yellow heartbeat that triggers every 5 seconds
    heartbeat = Timer.Alarm(blink_led, s=5, arg=(
        0x005500, 0.1, True), periodic=True)

    # Try to update RTC module with accurate UTC datetime if GPS is enabled and has not yet synchronized
    if gps_on and update_time_later:
        # Start a new thread to update time from gps if available
        _thread.start_new_thread(GpsSIM28.get_time, (rtc, status_logger))

except Exception as e:
    status_logger.exception("Exception in the main")
    led_lock.acquire()
    pycom.rgbled(0x550000)
    while True:
        time.sleep(5)
