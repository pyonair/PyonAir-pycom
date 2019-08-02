#!/usr/bin/env python
import pycom
from helper import blink_led

pycom.heartbeat(False)  # disable the heartbeat LED

# Try to initialize the RTC and mount SD card, if this fails, keep blinking red and do not proceed
try:
    from RtcDS1307 import clock
    from machine import SD
    import os
    from LoggerFactory import LoggerFactory
    from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
    # Initialise clock
    rtc = clock.get_time()

    # Mount SD card
    sd = SD()
    os.mount(sd, '/sd')

    # Initialise LoggerFactory and status logger
    logger_factory = LoggerFactory()
    status_logger = logger_factory.create_status_logger('status_logger', level=DEBUG, filename='status_log.txt')
except Exception as e:
    print(e)
    while True:
        blink_led(colour=0x770000, delay=0.5, count=1000)

pycom.rgbled(0x552000)  # flash orange until its loaded

# Initialize the rest
try:
    from machine import Pin, unique_id, Timer
    from ButtonPress import ButtonPress
    from SensorLogger import SensorLogger
    from Configuration import config
    from EventScheduler import EventScheduler
    import strings as s
    from helper import check_data_ready, blink_led, heartbeat
    from tasks import send_over_lora, flash_pm_averages
    from TempSHT35 import TempSHT35
    from new_config import new_config_thread
    from ubinascii import hexlify
    import _thread
    import time
    from initialisation import initialize_pm_sensor

    # Read configuration file to get preferences
    config.read_configuration(status_logger)

    user_button = ButtonPress(logger=status_logger)
    pin_14 = Pin("P14", mode=Pin.IN, pull=None)
    pin_14.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, user_button.press_handler)

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if not config.is_complete() or config.get_config("device_id") != device_id:
        config.reset_configuration(status_logger)
        #  Forces user to configure device, then reboot
        _thread.start_new_thread(new_config_thread, ('New_Config', status_logger, 300))

    # If device is correctly configured continue execution
    else:
        """SET VERSION NUMBER - version number is used to indicate the data format used to decode LoRa messages in the 
        back end. If the structure of the LoRa message is changed upon an update, increment the version number and 
        add a corresponding decoder to the back-end."""
        config.set_config({"version": 1})
        # Overwrite Preferences - DEVELOPER USE ONLY - keep all overwrites here
        config.set_config({"PM_interval": 1.5, "TEMP_interval": 5})

        # ToDo: get is_def having both sensors enabled
        # Clean up - process current file from previous boot or re-process process file if rebooted while processing
        is_def = check_data_ready()  # check which sensors are defined (enabled, and have data)
        flash_pm_averages(logger=status_logger, is_def=is_def)  # calculate averages for all defined sensors
        send_over_lora(logger=status_logger, is_def=is_def, timeout=60)  # send averages of defined sensors over LoRa

        TEMP_current = s.file_name_temp.format(s.TEMP, s.current_ext)
        TEMP_logger = SensorLogger(filename=TEMP_current, terminal_out=True)

        # Initialise temperature and humidity sensor thread with id: TEMP
        temp_sensor = TempSHT35(TEMP_logger, status_logger)
        status_logger.info("Temperature and humidity sensor initialized")

        # Initialise PM sensor threads
        if config.get_config(s.PM1):
            initialize_pm_sensor(sensor_name=s.PM1, pins=('P15', 'P11'), serial_id=1, status_logger=status_logger)
        if config.get_config(s.PM2):
            initialize_pm_sensor(sensor_name=s.PM2, pins=('P13', 'P18'), serial_id=2, status_logger=status_logger)

        # Start calculating averages for s.PM1 readings, and send data over LoRa
        PM_Events = EventScheduler(rtc=rtc, logger=status_logger)

        status_logger.info("Initialization finished")

        # Initialize custom yellow heartbeat that triggers every 6 seconds
        heartbeat = Timer.Alarm(heartbeat, s=6, periodic=True)
        # Blink green twice to identify that the device has been initialised
        blink_led(colour=0x005500, count=2)

except Exception as e:
    status_logger.exception("Exception in the main")
    pycom.rgbled(0x770000)
