import time
from TempSHT35 import TempSHT35
from configuration import config


class TempException(Exception):
    """
    Exception to be thrown if the temp & hum sensor reading fails
    """


def Temp_thread(thread_name, sensor_logger, status_logger):

    status_logger.info("Thread: {} started".format(thread_name))

    sensor = TempSHT35()
    sensor_id = config["TEMP_id"]
    timestamp_template = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"  # yyyy-mm-dd hh-mm-ss

    # read and log pm sensor data
    while True:

        timestamp = timestamp_template.format(*time.gmtime())  # get current time in desired format
        try:
            read_lst = sensor.read()  # read SHT35 sensor - [celsius, humidity] to ~5 significant figures
            round_lst = [round(x, 1) for x in read_lst]  # round readings to 1 significant figure
            str_round_lst = list(map(str, round_lst))  # cast float to string
            lst_to_log = [timestamp] + [sensor_id] + str_round_lst
            line_to_log = ','.join(lst_to_log)
            sensor_logger.log_row(line_to_log)
        except Exception as e:
            status_logger.exception(str(e))
            status_logger.critical("Failed to read from temperature and humidity sensor")
            continue
        finally:
            time.sleep(int(config["TEMP_interval"]))
