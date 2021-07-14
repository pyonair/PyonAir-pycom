
#!/usr/bin/env python
#import pdb # python debugger
import os
import time
import pycom
#PYBYTES
from _pybytes import Pybytes
from _pybytes_config import PybytesConfig


from machine import RTC, unique_id
from machine import SD, Pin, reset
import network # Used to disable WiFi
from initialisation import initialisation #initialise_time # TODO: clunky refactor
from helper import blink_led

import loggingpycom 
from LoggerFactory import LoggerFactory

from UserButton import UserButton

from Constants import *


from machine import Timer
from SensorLogger import SensorLogger
from EventScheduler import EventScheduler
from helper import blink_led, get_sensors, led_lock
from averages import get_sensor_averages
from TempSHT35 import TempSHT35
import GpsSIM28
import _thread
#from initialisation import initialise_pm_sensor, initialise_file_system, remove_residual_files, get_logging_level
from LoRaWAN import LoRaWAN


from machine import RTC, unique_id
#from initialisation import initialise_time
from ubinascii import hexlify
import Configuration
from new_config import new_config
from software_update import software_update
import strings as s
import ujson


#===================Disable default wifi===================

try:
    wlan = network.WLAN()
    wlan.deinit()
except Exception as e:
    print("Unable to disable WiFi")

#===============LED
pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange to indicate startup


#=========================Mount SD card=======
try:
    sd = SD()
    os.mount(sd, '/sd')
    #TODO: Error catch , set led for no SD card
except Exception as e:
    print("SD did not mount")


#===================Get a logger up and running asap!
logger_factory = LoggerFactory()
#TODO: Set log level to level in config file
status_logger = logger_factory.create_status_logger(DEFAULT_LOG_NAME, level=loggingpycom.DEBUG, terminal_out=True,
                                                        filename=LOG_FILENAME)

#=============Global config

config = Configuration.Configuration(status_logger)


#=========================Get time sorted
    # Get current time
rtc = RTC()
no_time, update_time_later =  initialisation(config, status_logger).initialise_time(rtc, False) #Dont use GPS , yet - just read RTC
update_time_later = True #Force a gps fix

#===============log  reboot


status_logger.warning("Rebooted")

#======================== Setup user interupt button
user_button = UserButton(status_logger)
pin_14 = Pin("P14", mode=Pin.IN, pull=Pin.PULL_DOWN)
pin_14.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING, user_button.button_handler)





#TODO: provision if key on sd card

#set connect to false in config file?

#========Pybytes
pycom.nvs_set('pybytes_debug',99 ) #0 warning - 99 all
conf = PybytesConfig().read_config()

pybytes = Pybytes(conf)
#backup config
#naw.... pybytes.write_config([file=’/flash/pybytes_config.json’, silent=False])

pybytes.update_config('pybytes_autostart', False, permanent=True, silent=False, reconnect=False)

status_logger.warning("Update")
#pdb.set_trace()
pycom.pybytes_on_boot(False)
conf = PybytesConfig().read_config()

pybytes = Pybytes(conf)

#TIME
# Get current time
#rtc = RTC()
#no_time, update_time_later = initialise_time(rtc, True, status_logger) #TODO: True is use gps


pybytes.start(autoconnect=False)
pybytes.send_signal(1, 0) # Sort of similar to uptime, sent to note reboot


#==========================






# Try to mount SD card, if this fails, keep blinking red and do not proceed
#try:
   
    
    #from loggingpycom import DEBUG
    #from LoggerFactory import LoggerFactory
    #from UserButton import UserButton#
    # Initialise LoggerFactory and status logger
    #logger_factory = LoggerFactory()
    #status_logger = logger_factory.create_status_logger(DEFAULT_LOG_NAME, level=loggingpycom.DEBUG, terminal_out=True,
    #                                                    filename=LOG_FILENAME)

    # Initialise button interrupt on pin 14 for user interaction
    #user_button = UserButton(status_logger)
    #pin_14 = Pin("P14", mode=Pin.IN, pull=Pin.PULL_DOWN)
    #pin_14.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING, user_button.button_handler)

    # Mount SD card
    #sd = SD()
    #os.mount(sd, '/sd')

# except Exception as e:
#     print(str(e))    
#     reboot_counter = 0
#     while True:
#         blink_led((0x550000, 0.5, True))  # blink red LED
#         time.sleep(0.5)
#         reboot_counter += 1
#         if reboot_counter >= 180:
#             reset()

try:


    # Read configuration file to get preferences
    #config = Configuration.Configuration(status_logger)
    #config.read_configuration() #Now removed from init

    """SET CODE VERSION NUMBER - if new tag is added on git, update code version number accordingly"""
    # ToDo: Update OTA.py so if version is 0.0.0, it backs up all existing files, and adds all files as new.
    # ToDo: Set code_version to '0.0.0' in default config, and remove the line below
    config.save_config({"code_version": "0.2.6"})

    """SET FORMAT VERSION NUMBER - version number is used to indicate the data format used to decode LoRa messages in
    the back end. If the structure of the LoRa message is changed during update, increment the version number and
    add a corresponding decoder to the back-end."""
    config.save_config({"fmt_version": 1})

    #TODO: Repair overrride later
    # Override Preferences - DEVELOPER USE ONLY - keep all overwrites here
    # if 'debug_config.json' in os.listdir('/flash'):
    #     status_logger.warning("Overriding configuration with the content of debug_config.json")
    #     with open('/flash/debug_config.json', 'r') as f:
    #         config.set_config(ujson.loads(f.read()))
    #         status_logger.warning("Configuration changed to: " + str(config.get_config()))

    # Check if GPS is enabled in configurations
    
    if config.get_config("GPS") == "OFF":
        gps_on = False
    else:
        gps_on = True



    #=======REmove this config stuff === warn this devide id may be used -- check
    # Check if device is configured, or SD card has been moved to another device
    # device_id = hexlify(unique_id()).upper().decode("utf-8")
    # if not config.is_complete(status_logger) or config.get_config("device_id") != device_id:
    #     config.reset_configuration(status_logger)
    #     #  Force user to configure device, then reboot
    #     new_config(status_logger, arg=0)
    #=======REmove this config stuff


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
        new_config(status_logger, arg=0) #TODO remove this
    except Exception:
        reset()

pycom.rgbled(0x552000)  # flash orange until its loaded

# If sd, time, logger and configurations were set, continue with initialisation
try:


    # Configurations are entered parallel to main execution upon button press for 2.5 secs
    user_button.set_config_blocking(False)

    # Set debug level - has to be set after logger was initialised and device was configured
    logger_factory.set_level(DEFAULT_LOG_NAME, initialisation(status_logger).get_logging_level())

    # Initialise file system
    initialisation(status_logger).initialise_file_system()

    # Remove residual files from the previous run (removes all files in the current and processing dir)
    initialisation(status_logger).remove_residual_files()

    # Get a dictionary of sensors and their status
    sensors = get_sensors(status_logger)

    # Join the LoRa network
    lora = False
    if (True in sensors.values() or gps_on) and config.get_config("LORA") == "ON":
        lora = LoRaWAN(status_logger)

    # Initialise temperature and humidity sensor thread with id: TEMP
    if sensors[s.TEMP]:
        TEMP_logger = SensorLogger(sensor_name=s.TEMP, terminal_out=True)
        if config.get_config(s.TEMP) == "SHT35":
            temp_sensor = TempSHT35(config, TEMP_logger, status_logger)
    status_logger.info("Temperature and humidity sensor initialised")

    # Initialise PM power circuitry
    PM_transistor = Pin('P20', mode=Pin.OUT)
    
    if config.get_config(s.PM1) == "OFF" and config.get_config(s.PM2) == "OFF": #Turn on sensors (power)
        PM_transistor.value(0) #TODO: Somehow make this clear that it disables BOTH??? 
    else:
        #FIX PM_transistor.value(1)
        status_logger.info("Power ON both PM sensors")

    # Initialise PM sensor threads
    if False: #sensors[s.PM1]:
        initialisation(status_logger).initialise_pm_sensor(sensor_name=s.PM1, pins=('P3', 'P17'), serial_id=1, status_logger=status_logger)
    if False: #sensors[s.PM2]:
        initialisation(status_logger).initialise_pm_sensor(sensor_name=s.PM2, pins=('P11', 'P18'), serial_id=2, status_logger=status_logger)

    # Start scheduling lora messages if any of the sensors are defined
    if True in sensors.values():
        PM_Events = EventScheduler(logger=status_logger, data_type="sensors", lora=lora)
    if gps_on:
        GPS_Events = EventScheduler(logger=status_logger, data_type="gps", lora=lora)

    status_logger.info("Initialisation finished")

    # Blink green three times to identify that the device has been initialised
    for val in range(3):
        blink_led((0x005500, 0.5, True))
        time.sleep(0.5)
    # Initialise custom yellow heartbeat that triggers every 5 seconds
    heartbeat = Timer.Alarm(blink_led, s=5, arg=(0x005500, 0.1, True), periodic=True)

    # Try to update RTC module with accurate UTC datetime if GPS is enabled and has not yet synchronized
    if gps_on and update_time_later:
        # Start a new thread to update time from gps if available
        # https://docs.pycom.io/firmwareapi/micropython/_thread/
        status_logger.info("Starting GPS thread...")
        _thread.start_new_thread(GpsSIM28.SetRTCtime, (rtc, status_logger))

except Exception as e:
    status_logger.exception("Exception in the main")
    led_lock.acquire()
    pycom.rgbled(0x550000)
    while True:
        time.sleep(5)
