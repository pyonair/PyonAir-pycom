#!/usr/bin/env python
import pycom
pycom.heartbeat(False)  # disable the heartbeat LED
pycom.rgbled(0x552000)  # flash orange until its loaded

try:
    from machine import RTC, Timer, SD, Pin, unique_id
    from RtcDS1307 import clock
    from ButtonPress import ButtonPress
    from LoggerFactory import LoggerFactory
    from SensorLogger import SensorLogger
    from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
    from configuration import read_configuration, reset_configuration, config
    from EventScheduler import EventScheduler
    import strings as s
    from helper import check_data_ready, blink_led
    from tasks import send_over_lora, flash_pm_averages
    from TempSHT35 import TempSHT35
    from new_config import config_thread
    from ubinascii import hexlify
    import _thread
    import os
    import time
    from initialisation import initialize_pm_sensor

    # Initialise clock
    rtc = clock.get_time()

    # Mount SD card
    sd = SD()
    os.mount(sd, '/sd')

    # Initialise LoggerFactory and status logger
    logger_factory = LoggerFactory()
    status_logger = logger_factory.create_status_logger('status_logger', level=DEBUG, filename='status_log.txt')

    # Read configuration file to get preferences
    read_configuration(status_logger)

    user_button = ButtonPress(logger=status_logger)
    pin_14 = Pin("P14", mode=Pin.IN, pull=None)
    pin_14.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, user_button.press_handler)

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if "" in config.values() or config["device_id"] != device_id:
        reset_configuration(status_logger)
        #  Forces user to configure device, then reboot
        _thread.start_new_thread(config_thread, ('Config', status_logger, 300))

    # If device is correctly configured continue execution
    else:
        # Overwrite Preferences - DEVELOPER USE ONLY - keep all overwrites here
        config["PM_interval"] = 1.5  # minutes
        config["TEMP_interval"] = 5  # seconds

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
        if config[s.PM1]:
            initialize_pm_sensor(sensor_name=s.PM1, pins=('P15', 'P17'), serial_id=1, status_logger=status_logger)
        if config[s.PM2]:
            initialize_pm_sensor(sensor_name=s.PM2, pins=('P13', 'P18'), serial_id=2, status_logger=status_logger)

        # Start calculating averages for s.PM1 readings, and send data over LoRa
        PM_Events = EventScheduler(rtc=rtc, logger=status_logger)

        status_logger.info("Initialization finished")

        # Blink green twice and put the heartbeat back to identify that the device has been initialised
        blink_led(colour=0x005500, count=2)
except Exception as e:
    print(e)
    pycom.rgbled(0x770000)
