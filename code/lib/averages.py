"""
Tasks to be called by event scheduler
"""

import os
from helper import mean_across_arrays, minutes_of_the_month, blink_led, get_sensors, get_format, current_lock  #TODO: chenge this type of import

from Configuration import Configuration
#import strings as s
from Constants import TIME_ISO8601_FMT
import time


def get_sensor_averages(config, logger, lora):
    """
    Takes the averages of sensor readings and constructs a line to log to the SD card, terminal and lora buffer
    :param logger: status logger
    :type logger: LoggerFactory object
    :param lora: LoRaWAN object, False if lora is not enabled
    :type lora: LoRaWAN object
    """

    logger.debug("Calculating averages")

    # get a dictionary of sensors and their status
    sensors = get_sensors(config, logger)
    fmt = get_format(sensors)
    version = str( config.get_config("fmt_version"))
    timestamp = TIME_ISO8601_FMT.format(*time.gmtime())  # get current time in desired format
    minutes = str(minutes_of_the_month())  # get minutes past last midnight

    try:
        sensor_averages = {}
        for sensor_name in [s.TEMP, s.PM1, s.PM2]:
            if sensors[sensor_name]:
                sensor_averages.update(calculate_average(sensor_name, logger))

        # Append averages to the line to be sent over LoRa according to which sensors are defined.
        line_to_log = '{}' + fmt + ',' + version + ',' + minutes
        for sensor_name in [s.TEMP, s.PM1, s.PM2]:
            if sensors[sensor_name]:
                line_to_log += ',' + str(config.get_config(sensor_name + "_id")) + ',' + ','.join(sensor_averages[sensor_name + "_avg"]) + ',' + str(sensor_averages[sensor_name + "_count"])
        line_to_log += '\n'

        # Logs line_to_log to archive and places copies into relevant to_send folders
        log_averages(line_to_log.format(timestamp + ','))
        if lora is not False:
            year_month = timestamp[2:4] + "," + timestamp[5:7] + ','
            lora.lora_buffer.write(line_to_log.format(year_month))

        # If raw data was processed, saved and dumped, processing files can be deleted
        path = s.processing_path
        for sensor_name in [s.TEMP, s.PM1, s.PM2]:
            if sensors[sensor_name]:
                filename = sensor_name + '.csv'
                try:
                    os.remove(path + filename)
                except Exception as e:
                    pass

    except Exception as e:
        logger.exception("Failed to flash averages")
        blink_led((0x550000, 0.4, True))


def calculate_average(sensor_name, config, logger):
    """
    Calculates averages for specific columns of sensor data to be sent over LoRa. Sets placeholders if it fails.
    :param sensor_name: PM1, PM2 or TEMP
    :type sensor_name: str
    :param logger: status logger
    :type logger: LoggerFactory object
    """

    filename = sensor_name + '.csv'
    sensor_type = config.get_config(sensor_name)
    sensor_id = str(config.get_config(sensor_name + "_id"))
    # headers in current file of the sensor according to its type
    headers = s.headers_dict_v4[sensor_type]

    # data to send if no readings are available
    avg_readings_str = list('0' * len(s.lora_sensor_headers[sensor_type]))
    count = 0

    try:
        with current_lock:
            # Move sensor_name.csv from current dir to processing dir
            os.rename(s.current_path + filename, s.processing_path + filename)

            with open(s.processing_path + filename, 'r') as f:
                # read all lines from processing
                lines = f.readlines()
                lines_lst = []  # list of lists that store average sensor readings from specific columns
                for line in lines:
                    stripped_line = line[:-1]  # strip \n
                    stripped_line_lst = str(stripped_line).split(',')  # split string to list at comas
                    named_line = dict(zip(headers, stripped_line_lst))  # assign each value to its header
                    sensor_reading = []
                    for header in s.lora_sensor_headers[sensor_type]:
                        sensor_reading.append(int(named_line[header]))
                    # Append extra lines here for more readings - update version number and back-end to interpret data
                    lines_lst.append(sensor_reading)
                    count += 1

                # Compute averages from sensor_name.csv.processing
                avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]

                # Append content of sensor_name.csv.processing into sensor_name.csv
                with open(s.archive_path + sensor_name + '_' + sensor_id + '.csv', 'a') as f:
                    for line in lines:
                        f.write(line)

    except Exception as e:
        logger.error("No readings from sensor {}".format(sensor_name))
        logger.warning("Setting 0 as a place holder")
        blink_led((0x550000, 0.4, True))
    finally:
        return {sensor_name + "_avg": avg_readings_str, sensor_name + "_count": count}


def log_averages(line_to_log):
    """
    Logs averages to the 'Averages' folder in 'Archive' separated by each month
    :param line_to_log: line of averages to log
    :type line_to_log: str
    """

    # Save averages to a new file each month
    archive_filename = "{:04d}_{:02d}".format(*time.gmtime()[:2]) + "_Sensor_Averages"  # yyyy_mm_Sensor_Averages
    archive_filepath = s.archive_averages_path + archive_filename + ".csv"  # /sd/archive/Averages/archive_filename
    with open(archive_filepath, 'a') as f:
        f.write(line_to_log)
