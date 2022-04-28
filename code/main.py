#!/usr/bin/env python
# import pdb # python debugger
import _thread
import os
import time

# trunk-ignore(flake8/F401)
from logging import root

import Configuration
import GpsSIM28
import loggingpycom
import network  # Used to disable WiFi
import PybytesTransmit
import pycom

# trunk-ignore(flake8/F401)
import ujson

# trunk-ignore(flake8/F401)
from Constants import (
    DEFAULT_LOG_NAME,
    FILENAME_FMT,
    GPS,
    LOG_EXT,
    LOG_FILENAME,
    PM1,
    PM2,
    RING_BUFFER_DIR,
    RING_BUFFER_FILE,
    TEMP,
    lora_file_name,
    processing_path,
)

# from EventScheduler import EventScheduler
from helper import blink_led, get_sensors, led_lock, secOfTheMonth
from initialisation import initialisation  # initialise_time # TODO: clunky refactor
from LoggerFactory import LoggerFactory

# trunk-ignore(flake8/F401)
from machine import RTC, SD, Pin, Timer, reset, temperature, unique_id

# trunk-ignore(flake8/F401)
from new_config import new_config
from RingBuffer import RingBuffer
from RtcDS1307 import clock
from SensorLogger import SensorLogger

# trunk-ignore(flake8/F401)
from software_update import software_update

# from averages import get_sensor_averages
from TempSHT35 import TempSHT35

# from initialisation import initialise_time
# trunk-ignore(flake8/F401)
from ubinascii import hexlifys
from UserButton import UserButton

# from initialisation import initialise_pm_sensor, initialise_file_system, remove_residual_files, get_logging_level
# from LoRaWAN import LoRaWAN


##==== Do early , stop halting -- load on thread later
print("Starting...")

# from _pybytes_config import PybytesConfig
# from _pybytes import Pybytes
# conf = PybytesConfig().read_config()
# pybytes = Pybytes(conf)
# pybytes.update_config('pybytes_autostart', False, permanent=True, silent=False, reconnect=False)
# pybytes.activate("eyJhIjoiMjc0MWQ0ZWItMmRmMS00Mzg0LTkxMGQtMzIzMGI5MTE2N2M3IiwicyI6InB5b25haXIiLCJwIjoicHlvbmFpciJ9")
# ===================Disable default wifi===================

try:
    wlan = network.WLAN()
    wlan.deinit()
    print("Disable WiFi")
# trunk-ignore(flake8/F841)
except Exception as e:
    print("Unable to disable WiFi")

# ===============LED
pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange to indicate startup


##
# ====== get time from RTC regardless -- better than default -- later we will try gps

rtc = RTC()
# Get time from RTC module
rtcClock = clock.get_time()
rtc.init(rtcClock)  # Set Pycom time to RTC time
print(str(rtcClock))

# =========================Mount SD card=======
try:
    sd = SD()
    os.mount(sd, "/sd")
    # TODO: Error catch , set led for no SD card
# trunk-ignore(flake8/F841)
except Exception as e:
    print("============================")
    print("===   SD did not mount   ===")
    print("============================")
    # TODO: Add led warning :  this is a show stopper error

# ================ thread memory default 4096
_thread.stack_size(4096 * 3)  # default is 4096 (and also min!)

# ===================Get a logger up and running asap!
logger_factory = LoggerFactory()
# TODO: Set log level to level in config file
fileNameStr = LOG_FILENAME + FILENAME_FMT.format(*time.gmtime()) + LOG_EXT
print(fileNameStr)
status_logger = logger_factory.create_status_logger(
    DEFAULT_LOG_NAME, level=loggingpycom.DEBUG, terminal_out=True, filename=fileNameStr
)

status_logger.info("Rebooted")

# =============Global config

config = Configuration.Configuration(status_logger)
status_logger.info("Config loaded")

# =============Init functions

init = initialisation(config, status_logger)

# =========================Get time sorted
# Get current time
rtc = RTC()
# Get time from RTC module
# rtc.init(clock.get_time())
no_time, update_time_later = init.initialise_time(
    rtc, False
)  # Dont use GPS , yet - just read RTC
update_time_later = True  # Force a gps fix
status_logger.info(
    "RTC read"
)  # TODO: fix GPS and time in general -- remember to roll over logs if big change


# ======================== Setup user interupt button
user_button = UserButton(status_logger)
pin_14 = Pin("P14", mode=Pin.IN, pull=Pin.PULL_DOWN)
pin_14.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING, user_button.button_handler)
user_button.set_config_enabled(True)
status_logger.warning("User button enabled")


# TODO: provision if key on sd card

# set connect to false in config file?


# ==========================


try:

    # Read configuration file to get preferences
    # config = Configuration.Configuration(status_logger)
    # config.read_configuration() #Now removed from init

    """SET CODE VERSION NUMBER - if new tag is added on git, update code version number accordingly"""
    # ToDo: Update OTA.py so if version is 0.0.0, it backs up all existing files, and adds all files as new.
    # ToDo: Set code_version to '0.0.0' in default config, and remove the line below
    config.save_config({"code_version": "0.2.6"})

    """SET FORMAT VERSION NUMBER - version number is used to indicate the data format used to decode LoRa messages in
    the back end. If the structure of the LoRa message is changed during update, increment the version number and
    add a corresponding decoder to the back-end."""
    config.save_config({"fmt_version": 1})

    # Check if GPS is enabled in configurations
    gps_on = config.get_config("GPS") != "OFF"

    # =======Remove this config stuff === warn this devide id may be used -- check
    # Check if device is configured, or SD card has been moved to another device
    # device_id = hexlify(unique_id()).upper().decode("utf-8")
    # if not config.is_complete(status_logger) or config.get_config("device_id") != device_id:
    #     config.reset_configuration(status_logger)
    #     #  Force user to configure device, then reboot
    #     new_config(status_logger, arg=0)
    # =======Remove this config stuff

    # User button will enter configurations page from this point on

    # # If initialise time failed to acquire exact time, halt initialisation
    # if no_time:
    #     raise Exception("Could not acquire UTC timestamp")

    # # Check if updating was triggered over LoRa
    # if config.get_config("update"):
    #     software_update(status_logger)

except Exception as e:
    status_logger.exception(str(e))
    # reboot_counter = 0
    # try:
    #     while user_button.get_reboot():
    #         blink_led((0x555500, 0.5, True))  # blink yellow LED
    #         time.sleep(0.5)
    #         reboot_counter += 1
    #         if reboot_counter >= 180:
    #             status_logger.info("rebooting...")
    #             reset()
    #     new_config(status_logger, arg=0) #TODO remove this
    # except Exception:
    #     reset()

pycom.rgbled(0x552000)  # flash orange until its loaded

# If sd, time, logger and configurations were set, continue with initialisation
try:

    status_logger.info("Filesystem.......")
    # Configurations are entered parallel to main execution upon button press for 2.5 secs
    user_button.set_config_blocking(False)
    # status_logger.debug(DEFAULT_LOG_NAME + "  :LOG_LEVEL_KEY" + config.get_config(LOG_LEVEL_KEY))
    # Set debug level - has to be set after logger was initialised and device was configured
    # status_logger = logger_factory.set_level(DEFAULT_LOG_NAME, config.get_config(LOG_LEVEL_KEY) ) # Cannot change mid way?
    # print("HERE")
    status_logger.info("Filesystem init start")
    # print("HERE2")
    init.remove_residual_files()
    # Initialise file system
    init.initialise_file_system()

    # Remove residual files from the previous run (removes all files in the current and processing dir)

    status_logger.info("Filesystem init completed")
    # Get a dictionary of sensors and their status
    sensors = get_sensors(config, status_logger)

    # Join the LoRa network
    # lora = False
    # if (True in sensors.values() or gps_on) and config.get_config("LORA") == "ON":  #TODO: lorawan disabled here
    #    lora = LoRaWAN(status_logger)

    ## Ring buffer
    message_limit_count = 5  # buffer size?
    cell_size_bytes = 100  # all buffer slots are a fixed size ! so waste space, but dont make this smaller that a max message!
    msgBuffer = RingBuffer(
        RING_BUFFER_DIR,
        RING_BUFFER_FILE,
        message_limit_count,
        cell_size_bytes,
        config,
        status_logger,
    )  # processing_path, lora_file_name, 31 * self.message_limit, 100)
    msgBuffer.push([1, secOfTheMonth()])  # port 1 , reboot 1

    ## Pybytes
    try:
        # Start PM sensor thread
        pyBytesThreadId = _thread.start_new_thread(
            PybytesTransmit.pybytes_thread, (msgBuffer, config, status_logger)
        )
        status_logger.info("THREAD - Pybytes  initialised")
    # trunk-ignore(flake8/F841)
    except Exception as e:
        status_logger.info("Failed to initialise Pybytes thread ")
        # raise e

    # Initialise temperature and humidity sensor thread with id: TEMP
    status_logger.info("Starting Temp logger...")
    if sensors[TEMP]:
        TEMP_logger = SensorLogger(sensor_name=TEMP, terminal_out=True)
        if config.get_config(TEMP) == "SHT35":
            temp_sensor = TempSHT35(config, TEMP_logger, status_logger)
    status_logger.info("Temperature and humidity sensor initialised")

    # Initialise PM power circuitry
    PM_transistor = Pin("P20", mode=Pin.OUT)

    if (
        config.get_config(PM1) == "OFF" and config.get_config(PM2) == "OFF"
    ):  # Turn on sensors (power)
        PM_transistor.value(0)  # TODO: Somehow make this clear that it disables BOTH???
    else:
        PM_transistor.value(1)
        status_logger.info("Enable power on for BOTH PM sensors")

    # Initialise PM sensor threads
    if sensors[PM1]:
        init.initialise_pm_sensor(
            sensor_name=PM1, pins=("P3", "P17"), serial_id=1, msgBuffer=msgBuffer
        )
    if sensors[PM2]:
        init.initialise_pm_sensor(
            sensor_name=PM2, pins=("P11", "P18"), serial_id=2, msgBuffer=msgBuffer
        )

    # Blink green three times to identify that the device has been initialised
    for val in range(3):
        blink_led((0x005500, 0.5, True))
        time.sleep(0.5)
    # Initialise custom yellow heartbeat that triggers every 5 seconds
    heartbeat = Timer.Alarm(blink_led, s=5, arg=(0x005500, 0.1, True), periodic=True)

    # Try to update RTC module with accurate UTC datetime if GPS is enabled and has not yet synchronized
    if (
        False
    ):  #  gps_on and update_time_later: #TODO: gps bugs, but rememebr shared serial so check logger file!
        # Start a new thread to update time from gps if available
        # https://docs.pycom.io/firmwareapi/micropython/_thread/
        status_logger.info("Starting GPS thread...")
        _thread.start_new_thread(GpsSIM28.SetRTCtime, (rtc, config, status_logger))

    status_logger.info("Initialisation finished")
    temp = (temperature() - 32) / 1.8
    status_logger.info("Memory:  " + str(pycom.get_free_heap()) + " Temp: " + str(temp))
    # TODO:  delete init object?
# trunk-ignore(flake8/F841)
except Exception as e:
    status_logger.exception("Exception in the main")
    led_lock.acquire()
    pycom.rgbled(0x550000)
    while True:
        time.sleep(5)
# #===================Disable default wifi===================

# try:
#     wlan = network.WLAN()
#     wlan.deinit()
#     print("Disable WiFi")
# except Exception as e:
#     print("Unable to disable WiFi")
