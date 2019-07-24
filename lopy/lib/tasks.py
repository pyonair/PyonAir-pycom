"""
Tasks to be called by event scheduler
"""

import uos
from helper import mean_across_arrays, minutes_from_midnight
import _thread
from LoRa_thread import lora_thread
from configuration import config
import strings as s


def send_over_lora(logger, timeout):
    """
    :param sensor_name: name of the sensor whose data is to be sent over LoRa
    :param logger:  general status logger
    :param timeout:  timeout for LoRa connection given in seconds
    """

    _thread.start_new_thread(lora_thread, ('LoRa', logger, timeout))


def flash_pm_averages(logger):
    """
    Reads csv file with PM sensor readings, computes averages for every column (apart timestamp) and appends
    the averages with the current timestamp into dump csv file.
    1) Rename sensor_name.csv.current to sensor_name.csv.processing
    2) Read all the data from sensor_name.csv.processin file
    3) Compute averages from sensor_name.csv.processing
    4) Append computed averages to sensor_name.csv.tosend
    5) Append content of sensor_name.csv.processing into sensor_name.csv
    6) Delete sensor_name.csv.processing
    """

    logger.info("Calculating averages over {} minute interval".format(config["PM_interval"]))

    header = s.headers_dict_v4["PM5003"]

    if config["PM1"]:
        PM1_avg_readings_str = get_lines(s.PM1_processing, s.PM1_current, s.PM1_dump, header, logger)

    if config["PM2"]:
        PM2_avg_readings_str = get_lines(s.PM2_processing, s.PM2_current, s.PM2_dump, header, logger)

    # Append computed averages to sensor_name.csv.tosend
    if (config["PM1"] and config["PM2"]):
        line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM1_id"]) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(config["PM2_id"]) + ',' + ','.join(PM2_avg_readings_str) + '\n'
    elif config["PM1"]:
        line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM1_id"]) + ',' + ','.join(PM1_avg_readings_str) + '\n'
    elif config["PM2"]:
        line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM2_id"]) + ',' + ','.join(PM2_avg_readings_str) + '\n'

    with open(s.lora_tosend, 'w') as f_tosend:  # TODO: change permission to 'a', hence make a queue for sending
        f_tosend.write(line_to_append)


def get_lines(processing, current, dump, header, logger):

    # Rename sensor_name.csv.current to sensor_name.csv.processing
    # logger.info('renaming ' + current + ' to ' + processing)
    try:
        uos.remove(processing)  # TODO: instead of removing, find a better way to deal with this
    except Exception:
        pass
    uos.rename(current, processing)

    # Read all the lines from sensor_name.csv.current
    f = open(processing, 'r')
    lines = f.readlines()
    f.close()
    lines_lst = []  # list of lists that store sensor readings without timestamps and sensor_id [[readingA1, readingB1,..], [readingA2,..]]
    for line in lines:
        stripped_line = line[:-1]  # strip \n
        stripped_line_lst = str(stripped_line).split(',')
        named_line = dict(zip(header, stripped_line_lst))
        sensor_reading = []
        try:
            sensor_reading.append(int(named_line["PM10"]))
            sensor_reading.append(int(named_line["PM25"]))
            lines_lst.append(sensor_reading)
        except Exception as e:
            logger.warning(e)

    # Compute averages from sensor_name.csv.processing
    avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]

    # Append content of sensor_name.csv.processing into sensor_name.csv
    with open(dump, 'a') as f:
        for line in lines:
            f.write(line)
    f.close()
    # Delete sensor_name.csv.processing
    uos.remove(processing)

    return avg_readings_str

#
# ______________________________________________________________________________________________________
# # Rename sensor_name.csv.current to sensor_name.csv.processing
# # logger.info('renaming ' + current + ' to ' + processing)
# try:
#     uos.remove(s.PM1_processing)  # TODO: instead of removing, find a better way to deal with this
# except Exception:
#     pass
# uos.rename(s.PM1_current, s.PM1_processing)
#
# # Read all the lines from sensor_name.csv.current
# f = open(s.PM1_processing, 'r')
# lines = f.readlines()
# f.close()
# lines_lst = []  # list of lists that store sensor readings without timestamps [[readingA1, readingB1,..], [readingA2,..]]
# for line in lines:
#     stripped_line = line[:-1]  # strip \n
#     stripped_line_lst = str(stripped_line).split(',')
#     sensor_reading = []
#     try:
#         for sen_read in stripped_line_lst[2:]:  # strip timestamp and sensor id
#             sensor_reading.append(int(sen_read))
#         lines_lst.append(sensor_reading)
#     except Exception as e:
#         logger.warning(e)
#
# # Compute averages from sensor_name.csv.processing
# avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]
#
# # Append computed averages to sensor_name.csv.tosend
# line_to_append = str(minutes_from_midnight()) + ',' + str(sensor_id) + ',' + ','.join(avg_readings_str) + '\n'
# with open(s.lora_tosend, 'w') as f_tosend:  # TODO: change permission to 'a', hence make a queue for sending
#     f_tosend.write(line_to_append)
#
# # Append content of sensor_name.csv.processing into sensor_name.csv
# with open(s.PM1_dump, 'a') as f:
#     for line in lines:
#         f.write(line)
# f.close()
# # Delete sensor_name.csv.processing
# uos.remove(s.PM1_processing)
#
