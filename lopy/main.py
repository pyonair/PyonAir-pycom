#!/usr/bin/env python
import pycom
pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange until its loaded

try:
    from machine import RTC, Timer, SD, Pin, unique_id
    from RtcDS1307 import clock
    from PM_thread import pm_thread
    from ButtonPress import ButtonPress
    from LoggerFactory import LoggerFactory
    from SensorLogger import SensorLogger
    from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
    from configuration import read_configuration, reset_configuration, config
    from EventScheduler import EventScheduler
    from strings import PM1_processing, PM1_current, PM2_processing, PM2_current
    from new_config import config_thread
    from ubinascii import hexlify
    import _thread
    import os
    import time
    from keys import APP_EUI, APP_KEY  # temporary - for key overwrite


    # Initialise clock
    rtc = clock.get_time()

    # Mount SD card
    sd = SD()
    os.mount(sd, '/sd')

    # Initialise LoggerFactory and status logger
    logger_factory = LoggerFactory()
    status_logger = logger_factory.create_status_logger('status_logger', level=DEBUG, filename='status_log.txt')

    # Initialise interrupt on user button for configuration over wifi
    user_button = ButtonPress(logger=status_logger)

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
        config["PM2_interval"] = 2
        config["app_eui"] = APP_EUI
        config["app_key"] = APP_KEY

        if config["PM1"]:
            try:
                # Initialise logger for PM1 sensor
                PM1_logger = SensorLogger(filename=PM1_current, terminal_out=True)

                # Delete 'PM1.csv.processing' if it exists TODO: send the content over LoRa instead
                if PM1_processing in os.listdir():
                    status_logger.info(PM2_processing + 'already exists, removing it')
                    os.remove(PM2_processing)

                # Start 1st PM sensor thread with id: PM1
                _thread.start_new_thread(pm_thread, ('PM1', PM1_logger, status_logger, ('P15', 'P17'), 1))

                # Start calculating averages for PM1 readings, and send data over LoRa
                PM1_Events = EventScheduler(rtc, logger=status_logger, sensor_name='PM1')

                status_logger.info("Sensor PM1 initialized")

            except:
                status_logger.error("Failed to initialize sensor PM1")

        if config["PM2"]:
            try:
                # Initialise logger for PM2 sensor
                PM2_logger = SensorLogger(filename=PM2_current, terminal_out=True)

                # Delete 'PM2.csv.processing' if it exists TODO: send the content over LoRa instead
                if PM2_processing in os.listdir():
                    status_logger.info(PM2_processing + 'already exists, removing it')
                    os.remove(PM2_processing)

                # Start 2nd PM sensor thread with id: PM2
                _thread.start_new_thread(pm_thread, ('PM2', PM2_logger, status_logger, ('P13', 'P18'), 2))

                # Start calculating averages  of PM2 readings, and send data over LoRa
                PM2_Events = EventScheduler(rtc, logger=status_logger, sensor_name='PM2')

                status_logger.info("Sensor PM2 initialized")

            except:
                status_logger.error("Failed to initialize sensor PM2")

        pin_14 = Pin("P14", mode=Pin.IN, pull=None)
        pin_14.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, user_button.press_handler)

        status_logger.info("Initialization finished")
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
