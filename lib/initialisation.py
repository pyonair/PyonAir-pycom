from RtcDS1307 import clock
import GpsSIM28
from network import LoRa
import socket
import ubinascii
from Configuration import config
from PM_thread import pm_thread
from SensorLogger import SensorLogger
import _thread
import strings as s
import os


def initialize_time(rtc, logger):
    no_time = False
    update_time_later = True
    try:
        # Get time from RTC module
        rtc.init(clock.get_time())
        # RTC module is not calibrated
        try:
            if rtc.now()[0] < 2019 or rtc.now()[0] >= 2100:
                # Get time and calibrate RTC module via GPS
                if config.get_config("GPS") == "ON":
                    GpsSIM28.get_time(rtc, led=True, logger=logger)
                    update_time_later = False
                # Calibrate RTC module via WiFi Configurations and then reboot
                else:
                    logger.critical("Visit configurations page and press submit to set the RTC module")
                    no_time = True
        except Exception as e:  # No way of getting time
            logger.exception("Failed to get current time")
            no_time = True  # navigate to configurations with yellow LED
    # RTC module is not available
    except Exception as e:
        logger.exception("Failed to get time from RTC module")
        try:
            # Get time via GPS
            if config.get_config("GPS") == "ON":
                GpsSIM28.get_time(rtc, led=True, logger=logger)
                update_time_later = False
            # No way of getting time
            else:
                no_time = True  # navigate to configurations with yellow LED
        except Exception as e:  # No way of getting time
            logger.exception("Failed to get current time")
            no_time = True  # navigate to configurations with yellow LED

    if no_time:
        logger.info("""Failed to get UTC timestamp from both the RTC and GPS modules.
                    Yellow light indicates that user has to connect and configure the device with GPS or RTC connected.
                    Possible issues and solutions:
                      RTC module is not connected - connect an RTC module and/or connect a GPS and enable its operation
                      GPS module is not connected - connect a GPS and enable its operation and/or connect an RTC module
                      RTC is not calibrated - simply press submit on configurations page
                      GPS is connected but not enabled - enable GPS on configurations page
                      GPS is enabled but not connected - connect a GPS module or have an RTC module connected and 
                        disable GPS on configurations page
                      GPS timeout - put device under clear sky and/or increase GPS timeout in configurations""")

    return no_time, update_time_later


def initialize_pm_sensor(sensor_name, pins, serial_id, status_logger):
    try:
        # Initialise sensor logger
        PM_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True)

        # Start PM sensor thread
        _thread.start_new_thread(pm_thread, (sensor_name, PM_logger, status_logger, pins, serial_id))

        status_logger.info("Sensor " + sensor_name + " initialized")
    except Exception as e:
        status_logger.exception("Failed to initialize sensor " + sensor_name)


def initialize_file_system():
    """
    Create directories for logging, processing, and sending data if they do not exist.
    """
    for directory in s.filesystem_dirs:
        if directory not in os.listdir(s.root_path):
            os.mkdir(s.root_path + directory)


def remove_residual_files():
    """
    Removes residual files from the last boot in the current and processing dirs
    """
    for path in [s.current_path, s.processing_path]:
        for file in os.listdir(path[:-1]):  # Strip '/' from the end of path
            os.remove(path + file)


def initialize_lorawan():
    # default region is Europe
    region = LoRa.EU868

    # set region according to configuration
    if config.get_config("region") == "Asia":
        region = LoRa.AS923
    elif config.get_config("region") == "Australia":
        region = LoRa.AU915
    elif config.get_config("region") == "United States":
        region = LoRa.US915

    lora = LoRa(mode=LoRa.LORAWAN, region=region, adr=True)

    # create an OTAA authentication parameters
    app_eui = ubinascii.unhexlify(config.get_config("application_eui"))
    app_key = ubinascii.unhexlify(config.get_config("app_key"))

    # join a network using OTAA (Over the Air Activation)
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

    # create a LoRa socket
    lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # request acknowledgment of data sent
    lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

    lora_socket.bind(1)

    # sets timeout for sending data
    lora_socket.settimeout(int(config.get_config("lora_timeout")) * 1000)

    return lora, lora_socket
