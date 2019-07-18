#!/usr/bin/env python
import pycom
pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange until its loaded

try:
    from machine import RTC, Timer, SD, Pin, unique_id
    from PM_thread import pm_thread
    from ButtonPress import ButtonPress
    import _thread
    import os
    from LoggerFactory import LoggerFactory
    from SensorLogger import SensorLogger
    from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
    from configuration import read_configuration, reset_configuration, config
    from EventScheduler import EventScheduler
    from new_config import config_thread
    from ubinascii import hexlify
    import time
    from keys import APP_EUI, APP_KEY


    # Provisional globals
    path = '/sd/'
    sensor_name = 'PM1'
    PM1_processing = path + sensor_name + '.csv.processing'

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
    sensor_logger = SensorLogger(filename=path + sensor_name + '.csv.current', terminal_out=True)

    # Read configuration file to get preferences
    read_configuration(status_logger)

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if "" in config.values() or config["device_id"] != device_id:
        reset_configuration(status_logger)
        #  Forces user to configure device, then reboot
        _thread.start_new_thread(config_thread, ('Config', status_logger, 300))

    # If device is correctly configured continue execution
    else:
        # Overwrite Preferences - DEVELOPER USE ONLY - keep all overwrites here
        config["PM1_interval"] = 2
        config["app_eui"] = APP_EUI
        config["app_key"] = APP_KEY

        # Delete 'PM1.csv.processing' if it exists TODO: send the content over LoRa instead
        if PM1_processing in os.listdir():
            status_logger.info(PM1_processing + 'already exists, removing it')
            os.remove(PM1_processing)

        # Start 1st PM sensor thread with id: PM1
        _thread.start_new_thread(pm_thread, (sensor_name, sensor_logger, status_logger))

        # Start calculating averages and sending data over LoRa
        PM1_Events = EventScheduler(rtc, logger=status_logger, sensor_name=sensor_name)

        # Initialise interrupt on user button for configuration over wifi
        user_button = ButtonPress(logger=status_logger)
        pin_14 = Pin("P14", mode=Pin.IN, pull=None)
        pin_14.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, user_button.press_handler)

        status_logger.info("Initialisation finished")
        # Blink green twice and put the heartbeat back to identify that the device has been initialised
        for i in range(2):
            pycom.rgbled(0x000000)
            time.sleep(0.5)
            pycom.rgbled(0x005500)
            time.sleep(0.5)
        pycom.heartbeat(True)
except Exception as e:
    print(e)
    pycom.rgbled(0x770000)
