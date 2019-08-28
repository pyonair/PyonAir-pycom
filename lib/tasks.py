"""
Tasks to be called by event scheduler
"""

import os
from helper import mean_across_arrays, minutes_from_midnight, blink_led
import _thread
from LoRa_thread import lora_thread
from Configuration import config
import strings as s
from helper import current_lock, processing_lock, archive_lock, tosend_lock


def send_over_lora(logger, lora, lora_socket):
    """
    Starts a thread that connects to LoRa and sends averages of the raw data
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    :param timeout: Timeout for LoRa to send over data seconds
    :type timeout: int
    """
    _thread.start_new_thread(lora_thread, ('LoRa', logger, lora, lora_socket))


def flash_pm_averages(logger):
    """
    Gets averages for specific columns of defined sensor data, loads them into a line and appends it to the file which
    the LoRa thread sends data from.
    A sensor is defined if it is ticked in the configuration and has data to be sent (has a current.csv file).
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    """

    sensors = {s.TEMP: True, s.PM1: False, s.PM2: False}
    if config.get_config(s.PM1) != "OFF":
        sensors[s.PM1] = True
    if config.get_config(s.PM2) != "OFF":
        sensors[s.PM2] = True

    # Only calculate averages at least one PM sensor is enabled
    if sensors[s.PM1] or sensors[s.PM2]:

        logger.debug("Calculating averages")

        try:
            TEMP_avg_readings_str, TEMP_count = get_averages(s.TEMP, logger)

            if sensors[s.PM1]:
                # Get averages for PM1 sensor
                PM1_avg_readings_str, PM1_count = get_averages(s.PM1, logger)

            if sensors[s.PM2]:
                # Get averages for PM2 sensor
                PM2_avg_readings_str, PM2_count = get_averages(s.PM2, logger)

            # Append averages to the line to be sent over LoRa according to which sensors are defined.
            if sensors[s.PM1] and sensors[s.PM2]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM1_id")) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(PM1_count) + ',' + str(config.get_config("PM2_id")) + ',' + ','.join(PM2_avg_readings_str) + ',' + str(PM2_count) + '\n'
            elif sensors[s.PM1]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM1_id")) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(PM1_count) + '\n'
            elif sensors[s.PM2]:
                line_to_append = str(config.get_config("version")) + ',' + str(minutes_from_midnight()) + ',' + str(config.get_config("TEMP_id")) + ',' + ','.join(TEMP_avg_readings_str) + ',' + str(TEMP_count) + ',' + str(config.get_config("PM2_id")) + ',' + ','.join(PM2_avg_readings_str) + ',' + str(PM2_count) + '\n'

            # Append lines to sensor_name.csv.tosend
            lora_filepath = s.lora_path + s.lora_file
            with open(lora_filepath, 'w') as f_tosend:
                f_tosend.write(line_to_append)

            # If raw data was processed, saved and dumped, processing files can be deleted
            with processing_lock:
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
            blink_led(colour=0x770000, delay=0.5, count=1)


def get_averages(sensor_name, logger):
    """
    Calculates averages for specific columns of a sensor log data to be sent over LoRa.
    :param sensor_name: sensor name
    :sensor_type sensor_name: str
    :return: average readings of specific columns
    :rtype: str
    """

    filename = sensor_name + '.csv'
    sensor_type = config.get_config(sensor_name)
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
                with archive_lock:
                    with open(s.archive_path + filename, 'a') as f:
                        for line in lines:
                            f.write(line)

    except Exception as e:
        # ToDo: Find out why exception logs the traceback 'None' here.
        logger.exception("No readings from sensor {}".format(sensor_name))
        logger.warning("Setting 0 as a place holder")
        blink_led(colour=0x770000, delay=0.5, count=1)
    finally:
        return avg_readings_str, count
