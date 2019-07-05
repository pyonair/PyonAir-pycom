"""
Tasks to be called by event scheduler
"""

import uos
from helper import mean_across_arrays, seconds_from_midnight


def flash_pm_averages(sensor_name, logger):
    """
    Reads csv file with PM sensor readings, computes averages for every column (apart timestamp) and appends
    the averages with the current timestamp into dump csv file.
    1) Rename sensor_name.csv.current to sensor_name.csv.processing
    2) Read all the data from sensor_name.csv.processin file
    3) Compute averages from sensor_name.csv.processing
    4) Append computed averages to sensor_name.csv.tosend
    5) Append content of sensor_name.csv.processing into sensor_name.csv
    6) Delete sensor_name.csv.processing
    7) Schedule to send all content of sensor_name.csv.tosend over LoRaWAN
    :param filename:
    :type filename: str
    """
    path = '/sd/'
    current = path + sensor_name + '.csv.current'
    processing = path + sensor_name + '.csv.processing'
    tosend = path + sensor_name + '.csv.tosend'
    dump = path + sensor_name + '.csv'

    # Rename sensor_name.csv.current to sensor_name.csv.processing
    logger.info('renaming ' + current + ' to ' + processing)
    try:
        uos.remove(processing)  # TODO: instead of removing, find a better way to deal with this
    except Exception:
        pass
    uos.rename(current, processing)

    # Read all the lines from sensor_name.csv.current
    f = open(processing, 'r')
    lines = f.readlines()
    f.close()
    lines_lst = []  # list of lists that store sensor readings without timestamps [[readingA1, readingB1,..], [readingA2,..]]
    for line in lines:
        stripped_line = line[:-1]  # strip \n
        stripped_line_lst = str(stripped_line).split(',')
        sensor_reading = [int(i) for i in stripped_line_lst[1:]]  # strip timestamp
        lines_lst.append(sensor_reading)

    # Compute averages from sensor_name.csv.processing
    avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]

    # Append computed averages to sensor_name.csv.tosend
    line_to_append = str(seconds_from_midnight()) + ',' + ','.join(avg_readings_str) + '\n'
    with open(tosend, 'w') as f_tosend:  # TODO: change permission to 'a', hence make a queue for sending
        f_tosend.write(line_to_append)

    # Append content of sensor_name.csv.processing into sensor_name.csv
    with open(dump, 'a') as f:
        for line in lines:
            f.write(line)
    f.close()
    # Delete sensor_name.csv.processing
    uos.remove(processing)
