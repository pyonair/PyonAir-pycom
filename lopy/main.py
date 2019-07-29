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
    from strings import file_name_temp, current_ext, processing_ext, PM1, PM2
    from new_config import config_thread
    from ubinascii import hexlify
    import _thread
    import os
    import time

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

    # Check if device is configured, or SD card has been moved to another device
    device_id = hexlify(unique_id()).upper().decode("utf-8")
    if "" in config.values() or config["device_id"] != device_id:
        reset_configuration(status_logger)
        #  Forces user to configure device, then reboot
        _thread.start_new_thread(config_thread, ('Config', status_logger, 300))

    # If device is correctly configured continue execution
    else:
        # Overwrite Preferences - DEVELOPER USE ONLY - keep all overwrites here
        config["PM_interval"] = 1.5

        def initialize_pm_sensor(sensor_name, pins, serial_id):
            try:
                filename_current = file_name_temp.format(sensor_name, current_ext)
                filename_processing = file_name_temp.format(sensor_name, processing_ext)
                # Initialise sensor logger

                PM_logger = SensorLogger(filename=filename_current, terminal_out=True)

                # Delete 'PM1.csv.processing' if it exists TODO: send the content over LoRa instead
                if filename_processing in os.listdir():  # TODO: This probably does not reach the necessary depth to check the file
                    status_logger.info(filename_processing + 'already exists, removing it')
                    os.remove(filename_processing)

                # Start 1st PM sensor thread with id: PM1
                _thread.start_new_thread(pm_thread, (sensor_name, PM_logger, status_logger, pins, serial_id))

                status_logger.info("Sensor " + sensor_name + " initialized")
                aas = 1/0
                print(aas)
            except Exception as e:
                status_logger.exception("Failed to initialize sensor " + sensor_name)

        if config["PM1"]:
            initialize_pm_sensor(sensor_name=PM1, pins=('P15', 'P17'), serial_id=1)

        if config["PM2"]:
            initialize_pm_sensor(sensor_name=PM2, pins=('P13', 'P18'), serial_id=2)

        # Start calculating averages for PM1 readings, and send data over LoRa
        PM_Events = EventScheduler(rtc=rtc, logger=status_logger)

        # Initialise interrupt on user button for configuration over wifi
        user_button = ButtonPress(logger=status_logger)
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
