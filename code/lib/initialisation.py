from RtcDS1307 import clock
import GpsSIM28
from PM_read import pm_thread
from loggingpycom import INFO, WARNING, CRITICAL, DEBUG, ERROR
#import Configuration
from Configuration import Configuration
import _thread
import strings as s
import os
import pycom
import RingBuffer
from Constants import RING_BUFFER_DIR , RING_BUFFER_FILE

class initialisation:

    def __init__(self, config,  logger):
        self.logger = logger
        self.config = config

    def initialise_time(self, rtc, gps_on):
        """
        Acquire UTC timestamp from RTC module or GPS
        :param rtc: pycom real time clock
        :type rtc: RTC object
        :param gps_on: True or False
        :type gps_on: bool
        :param logger: status logger
        :type logger: LoggerFactory object
        :return: no_time, update_time_later
        :rtype: bool, bool
        """

        no_time = False
        update_time_later = True
        try:
            # Get time from RTC module
            rtc.init(clock.get_time())
            # RTC module is not calibrated
            if rtc.now()[0] < 2019 or rtc.now()[0] >= 2100:
                # Get time and calibrate RTC module via GPS
                if gps_on:
                    logger.info("Attempt GPS ...")
                    if GpsSIM28.get_time(rtc, logger):
                        update_time_later = False
                    else:  # No way of getting time
                        logger.exception("Failed to get current time from GPS")
                        no_time = True  # navigate to configurations with yellow LED
                # Calibrate RTC module via WiFi Configurations and then reboot
                else:
                    logger.critical("Visit configurations page and press submit to set the RTC module")
                    no_time = True
        # RTC module is not available
        except Exception as e:
            logger.exception("Failed to get time from RTC module")
            # Get time via GPS
            if gps_on:
                if GpsSIM28.get_time(rtc, logger):
                    update_time_later = False
                else:  # No way of getting time
                    logger.exception("Failed to get current time from GPS")
                    no_time = True  # navigate to configurations with yellow LED
            else:  # No way of getting time
                no_time = True  # navigate to configurations with yellow LED

        if no_time:
            logger.info("""Failed to get UTC timestamp from both RTC and GPS modules.
                        User has to connect and configure the device with GPS or RTC connected.
                        Device will reboot in 3 minutes unless button is pressed for 3 seconds and device is configured.

                        Possible issues and solutions:
                        RTC module is not connected - connect an RTC module and/or connect a GPS and enable its operation
                        GPS module is not connected - connect a GPS and enable its operation and/or connect an RTC module
                        RTC is not calibrated - simply press submit on configurations page
                        GPS is connected but not enabled - enable GPS on configurations page
                        GPS is enabled but not connected - connect a GPS module or have an RTC module connected and
                            disable GPS on configurations page
                        GPS timeout - put device under clear sky and/or increase GPS timeout in configurations""")
        elif gps_on:
            pycom.rgbled(0x552000)  # flash orange until its loaded

        return no_time, update_time_later


    # def initialiseRingBuffer(self, config, logger):

    #     try:
    #         # Start buffer
    #         _thread.stack_size(4096 * 2) # default is 4096 (and slso min!)
    #         _thread.start_new_thread(RingBuffer.ringBufferThread, (config,  logger))  #TODO: move to main or similar


    #         self.logger.info("THREAD - Ring Buffer initialised")
    #     except Exception as e:
    #         logger.error("Failed to initialise Ring Buffer")
    #         logger.error(e)




    def initialise_pm_sensor(self, sensor_name, pins, serial_id, msgBuffer):
        """

        :param sensor_name: PM1 or PM2
        :type sensor_name: str
        :param pins: pins for serial bus (TX, RX)
        :type pins: tuple(int, int)
        :param serial_id: id for serial bus (0, 1 or 2)
        :type serial_id: int
        :param status_logger: status logger
        :type status_logger: LoggerFactory object
        """
        try:
            # Start PM sensor thread
            _thread.stack_size(4096 * 3) # default is 4096 (and slso min!)
            _thread.start_new_thread(pm_thread, (sensor_name, msgBuffer, self.config,  self.logger, pins, serial_id))  #TODO: move to main or similar


            self.logger.info("THREAD - Sensor " + sensor_name + " initialised")
        except Exception as e:
            self.exception("Failed to initialise sensor thread " + sensor_name)


    def initialise_file_system(self):
        """
        Create directories for logging, processing, archive, and sending data if they do not exist.
        """
        # Create directories in /sd/
        for directory in s.filesystem_dirs:
            if directory not in os.listdir(s.root_path):
                os.mkdir(s.root_path + directory)

        # Create Averages directory in /sd/Archive/ directory
        #if s.archive_averages not in os.listdir(s.root_path + s.archive):
        #    os.mkdir(s.archive_path + s.archive_averages)


    def remove_residual_files(self):
        """
        Removes residual files from the last boot in the current and processing dirs
        """
        #TODO: clean up ? do we need it now that there is no archive process?
        # for path in [s.current_path, s.processing_path]:
        #     for file in os.listdir(path[:-1]):  # Strip '/' from the end of path
        #         if file != s.lora_file_name:
        #             os.remove(path + file)

        # Debug : remove buffer file if to wipe queue
        # os.remove(RING_BUFFER_DIR + RING_BUFFER_FILE)
        pass
 

    # def get_logging_level(self):
    #     """
    #     Get logging level from configurations
    #     :return: logging level
    #     :rtype: str
    #     """
    #     logging_lvl = Configuration(self.logger).get_config("logging_lvl")
    #     if logging_lvl == "Critical":
    #         return CRITICAL
    #     elif logging_lvl == "Error":
    #         return ERROR
    #     elif logging_lvl == "Warning":
    #         return WARNING
    #     elif logging_lvl == "Info":
    #         return INFO
    #     elif logging_lvl == "Debug":
    #         return DEBUG
    #     #TODO: just use this in the config! dont translate