from plantowerpycom import Plantower, PlantowerException
from helper import mean_across_arrays


def pm_thread(sensor_name, sensor_logger, status_logger):

    status_logger.info("Thread: {} started".format(sensor_name))

    # variables for sensor reading and computing averages
    plantower = Plantower()
    last_timestamp = None
    sensor_readings_lst = []

    # read and log pm sensor data
    while True:

        try:
            recv = plantower.read()
            if recv:
                recv_lst = str(recv).split(',')
                curr_timestamp = recv_lst[0]
                sensor_reading = [int(i) for i in recv_lst[1:]]
                if curr_timestamp != last_timestamp:
                    # If there are any readings with the previous timestamps, process them
                    if len(sensor_readings_lst) > 0:
                        lst_to_log = [last_timestamp] + [str(int(i)) for i in mean_across_arrays(sensor_readings_lst)]
                        line_to_log = ','.join(lst_to_log)
                        sensor_logger.log_row(line_to_log)
                    # Set/reset global variables
                    last_timestamp = curr_timestamp
                    sensor_readings_lst = []
                # Add the current reading to the list, which will be processed when the timestamp changes
                sensor_readings_lst.append(sensor_reading)

        except PlantowerException as e:
            status_logger.error(e)
