"""
Tasks to be called by event scheduler
"""

import os
from helper import mean_across_arrays, minutes_from_midnight, blink_led
import _thread
from LoRa_thread import lora_thread
from Configuration import config
import strings as s
from helper import pm_current_lock, pm_processing_lock, pm_dump_lock, pm_tosend_lock
import time


class FlashPMAveragesException(Exception):
    pass


def send_over_lora(logger, is_def):
    """
    Starts a thread that connects to LoRa and sends averages of the raw data
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    :param timeout: Timeout for LoRa to send over data seconds
    :type timeout: int
    """
    _thread.start_new_thread(lora_thread, ('LoRa', logger, is_def))


def flash_pm_averages(logger, is_def):
    """
    Gets averages for specific columns of defined sensor data, loads them into a line and appends it to the file which
    the LoRa thread sends data from.
    A sensor is defined if it is ticked in the configuration and has data to be sent (has a current.csv file).
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    """
    # Only calculate averages if PM1 or PM2 or both sensors are enabled and have gathered data
    if is_def[s.PM1] or is_def[s.PM2]:

        logger.info("Calculating averages")

        try:
            try:
                TEMP_avg_readings_str, TEMP_count = get_averages(s.TEMP)
            except Exception as e:
                logger.exception("No readings from temperature sensor")
                logger.critical("Setting 9999 for both temperature and humidity as a place holder")
                TEMP_avg_readings_str = ["9999", "9999"]  # data to send if no temperature is available
                TEMP_count = 0

            if is_def[s.PM1]:
                # Get averages for PM1 sensor
                PM1_avg_readings_str, PM1_count = get_averages(s.PM1)

            if is_def[s.PM2]:
                # Get averages for PM2 sensor
                PM2_avg_readings_str, PM2_count = get_averages(s.PM2)

            # Append averages to the line to be sent over LoRa according to which sensors are defined.
            if is_def[s.PM1] and is_def[s.PM2]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM1_id")) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(PM1_count) + ',' + str(config.get_config("PM2_id")) + ',' + ','.join(PM2_avg_readings_str) + ',' + str(PM2_count) + '\n'
            elif is_def[s.PM1]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM1_id")) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(PM1_count) + '\n'
            elif is_def[s.PM2]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM2_id")) + ',' + ','.join(PM2_avg_readings_str) + ',' + str(PM2_count) + '\n'

            # Append lines to sensor_name.csv.tosend
            lora_filepath = s.lora_path + s.lora_file
            with open(lora_filepath, 'w') as f_tosend:
                f_tosend.write(line_to_append)

            # If raw data was processed, saved and dumped, processing files can be deleted
            with pm_processing_lock:
                path = s.processing_path
                for sensor_name in [s.TEMP, s.PM1, s.PM2]:
                    if is_def[sensor_name]:
                        filename = sensor_name + '.csv'
                        try:
                            os.remove(path + filename)
                        except Exception as e:
                            logger.exception("Failed to remove " + filename + " in " + path)

        except Exception as e:
            logger.exception("Failed to flash averages")
            blink_led(colour=0x770000, delay=0.5, count=1)


def get_averages(sensor_name):
    """
    Calculates averages for specific columns of a sensor log data to be sent over LoRa.
    :param sensor_name: sensor name
    :sensor_type sensor_name: str
    :return: average readings of specific columns
    :rtype: str
    """

    with pm_processing_lock:
        filename = sensor_name + '.csv'
        # Only process current readings if previous processing file was dealt with - if device is rebooted while
        # processing the data (processing file was not deleted) then process it again and send it over LoRa. In this
        # case current file has little to no data, so can be deleted - see else statement

        # If there is NO sensor_name.csv file in the PROCESSING dir
        if filename not in os.listdir(s.processing_path[:-1]):  # Strip '/' from the end of path
            # If there IS sensor_name.csv in the CURRENT dir
            if filename in os.listdir(s.current_path[:-1]):  # Strip '/' from the end of path
                # Move sensor_name.csv from current dir to processing dir
                os.rename(s.current_path + filename, s.processing_path + filename)
            # If there is no sensor_name.csv file in the current dir, then return (because there is nothing to process)
            else:
                raise FlashPMAveragesException("Cannot flash averages because there is no " + filename + " in " + s.current_path)

        # Header of current file
        sensor_type = config.get_config(sensor_name)
        header = s.headers_dict_v4[sensor_type]
        count = 0

        with open(s.processing_path + filename, 'r') as f:
            # read all lines from processing
            lines = f.readlines()
            lines_lst = []  # list of lists that store average sensor readings from specific columns
            for line in lines:
                stripped_line = line[:-1]  # strip \n
                stripped_line_lst = str(stripped_line).split(',')  # split string to list at comas
                named_line = dict(zip(header, stripped_line_lst))  # assign each value to its header
                sensor_reading = []
                if sensor_type == 'PMS5003' or sensor_type == 'SPS030':
                    sensor_reading.append(int(named_line["PM10"]))
                    sensor_reading.append(int(named_line["PM25"]))
                elif sensor_type == 'SHT35':
                    sensor_reading.append(int(float(named_line["temperature"])*10))  # shift left and cast to int
                    sensor_reading.append(int(float(named_line["humidity"])*10))  # shift left and cast to int
                # Append extra lines here for more readings - update version number and back-end to interpret data
                lines_lst.append(sensor_reading)
                count += 1

            # Compute averages from sensor_name.csv.processing
            avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]

            # Append content of sensor_name.csv.processing into sensor_name.csv
            with pm_dump_lock:
                with open(s.archive_path + filename, 'a') as f:
                    for line in lines:
                        f.write(line)

            return avg_readings_str, count
