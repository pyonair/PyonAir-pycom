#!/usr/bin/env python
import pycom
from helper import blink_led

pycom.heartbeat(False)  # disable the heartbeat LED

# Try to mount SD card, if this fails, keep blinking red and do not proceed
try:
    from machine import SD
    import os
    from loggingpycom import DEBUG
    from LoggerFactory import LoggerFactory

    # Mount SD card
    sd = SD()
    os.mount(sd, '/sd')

    # Initialise LoggerFactory and status logger
    logger_factory = LoggerFactory()
    status_logger = logger_factory.create_status_logger('status_logger', level=DEBUG, terminal_out=True,
                                                        filename='status_log.txt')
except Exception as e:
    print(str(e))
    while True:
        blink_led(colour=0x770000, delay=0.5, count=1000)

try:
    from machine import RTC, unique_id
    from initialisation import initialize_time
    from ubinascii import hexlify
    from Configuration import config
    from new_config import new_config
    from machine import Pin

    #ToDo: Proper implementation of transistor circuitry
    PMTR = Pin('P20', mode=Pin.OUT)
    PMTR.value(1)
    GPSTR = Pin('P19', mode=Pin.OUT)
    GPSTR.value(1)

    # Read configuration file to get preferences
    config.read_configuration()

    # Get current time
    rtc = RTC()
    no_time, update_time_later = initialize_time(rtc, status_logger)

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if not config.is_complete(status_logger) or config.get_config("device_id") != device_id:
        config.reset_configuration(status_logger)
        #  Force user to configure device, then reboot - yellow or blue LED depending if time is set
        new_config(status_logger, no_time)

    if no_time:  # configure with yellow LED - user has to connect an RTC or a GPS and configure
        new_config(status_logger, no_time)

except Exception as e:
    status_logger.exception("Failed to set time or configure the device")
    while True:
        blink_led(colour=0x770000, delay=0.5, count=1000)

pycom.rgbled(0x552000)  # flash orange until its loaded

# If sd, time, logger and configurations were set, continue with initializing non-critical features
try:
    from machine import Timer
    from ConfigButton import ConfigButton
    from SensorLogger import SensorLogger
    from EventScheduler import EventScheduler
    import strings as s
    from helper import blink_led, heartbeat, get_logging_level
    from tasks import send_over_lora, flash_pm_averages
    from TempSHT35 import TempSHT35
    import GpsSIM28
    import _thread
    import time
    from initialisation import initialize_pm_sensor, initialize_file_system, remove_residual_files, initialize_lorawan
    import ujson

    """SET VERSION NUMBER - version number is used to indicate the data format used to decode LoRa messages in the
    back end. If the structure of the LoRa message is changed during update, increment the version number and
    add a corresponding decoder to the back-end."""
    config.set_config({"version": 1})

    # Set debug level - has to be set after logger was initialized and device was configured
    logger_factory.set_level('status_logger', get_logging_level())

    # Override Preferences - DEVELOPER USE ONLY - keep all overwrites here
    if 'debug_config.json' in os.listdir('/flash'):
        status_logger.warning("Overriding configuration with the content of debug_config.json")
        with open('/flash/debug_config.json', 'r') as f:
            config.set_config(ujson.loads(f.read()))
            status_logger.warning("Configuration changed to: " + str(config.get_config()))

    # Initialize file system
    initialize_file_system()

    # Remove residual files from the previous run (removes all files in the current and processing dir)
    remove_residual_files()

    # ToDo: pin bounces and crashes program if board is not plugged in properly
    # Initialize button interrupt on pin 14 for entering configurations page
    config_button = ConfigButton(logger=status_logger)
    pin_14 = Pin("P14", mode=Pin.IN, pull=None)
    pin_14.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING, config_button.button_handler)

    # Try to update RTC module with accurate UTC datetime if GPS is enabled and has not yet synchronized
    # ToDo: When implementing GPS on bus 0 check if enabled not connected casues any issues
    if config.get_config("GPS") == "ON" and update_time_later:
        # Start a new thread to update time from gps if available
        _thread.start_new_thread(GpsSIM28.get_time, (rtc, False, status_logger))

    # Join the LoRa network
    lora, lora_socket = initialize_lorawan()

    # Initialise temperature and humidity sensor thread with id: TEMP
    if config.get_config(s.TEMP) != "OFF":
        TEMP_current = s.file_name_temp.format(s.TEMP, s.current_ext)
        TEMP_logger = SensorLogger(sensor_name=s.TEMP, terminal_out=True)
        if config.get_config(s.TEMP) == "SHT35":
            temp_sensor = TempSHT35(TEMP_logger, status_logger)
    status_logger.info("Temperature and humidity sensor initialized")

    # Initialise PM sensor threads
    if config.get_config(s.PM1) != "OFF":
        initialize_pm_sensor(sensor_name=s.PM1, pins=('P3', 'P17'), serial_id=1, status_logger=status_logger)
    if config.get_config(s.PM2) != "OFF":
        initialize_pm_sensor(sensor_name=s.PM2, pins=('P11', 'P18'), serial_id=2, status_logger=status_logger)

    # Start calculating averages for s.PM1 readings, and send data over LoRa
    PM_Events = EventScheduler(rtc=rtc, logger=status_logger, lora=lora, lora_socket=lora_socket)

    status_logger.info("Initialization finished")

    # Blink green twice to identify that the device has been initialised
    blink_led(colour=0x007700, count=2)
    # Initialize custom yellow heartbeat that triggers every 6 seconds
    heartbeat = Timer.Alarm(heartbeat, s=5, periodic=True)

except Exception as e:
    status_logger.exception("Exception in the main")
    pycom.rgbled(0x770000)
    while True:
        time.sleep(5)
