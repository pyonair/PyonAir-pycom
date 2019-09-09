"""
Tasks to be called by event scheduler
"""

import os
from helper import mean_across_arrays, minutes_of_the_month, blink_led, get_sensors, get_format, current_lock
from Configuration import config
import strings as s
import time


def get_sensor_averages(logger, lora):
    """
    Gets averages for specific columns of defined sensor data, loads them into a line and appends it to the file which
    the LoRa thread sends data from.
    A sensor is defined if it is ticked in the configuration and has data to be sent (has a current.csv file).
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    """

    logger.debug("Calculating averages")

    # get a dictionary of sensors and their status
    sensors = get_sensors()
    fmt = get_format(sensors)
    version = str(config.get_config("version"))
    timestamp = s.csv_timestamp_template.format(*time.gmtime())  # get current time in desired format
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
        if config.get_config("LORA") == "ON":
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
                    logger.exception("Failed to remove " + filename + " in " + path)

    except Exception as e:
        logger.exception("Failed to flash averages")
        blink_led((0x550000, 0.4, True))


def calculate_average(sensor_name, logger):
    """
    Calculates averages for specific columns of a sensor log data to be sent over LoRa.
    :param sensor_name: sensor name
    :sensor_type sensor_name: str
    :return: average readings of specific columns
    :rtype: str
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
        logger.exception("No readings from sensor {}".format(sensor_name))
        logger.warning("Setting 0 as a place holder")
        blink_led((0x550000, 0.4, True))
    finally:
        return {sensor_name + "_avg": avg_readings_str, sensor_name + "_count": count}


def log_averages(line_to_log):

    # Save averages to a new file each month
    archive_filename = "{:04d}_{:02d}".format(*time.gmtime()[:2]) + "_Sensor_Averages"  # yyyy_mm_Sensor_Averages
    archive_filepath = s.archive_averages_path + archive_filename + ".csv"  # /sd/archive/Averages/archive_filename
    with open(archive_filepath, 'a') as f:
        f.write(line_to_log)
