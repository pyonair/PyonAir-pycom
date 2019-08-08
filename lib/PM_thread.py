from plantowerpycom import Plantower, PlantowerException
from sensirionpycom import Sensirion, SensirionException
from helper import mean_across_arrays, blink_led
from Configuration import config
import time


# ToDo: Use interrupts and unify the two sensor processing by polling only one reading from the plantower in a second.
def pm_thread(sensor_name, sensor_logger, status_logger, pins, serial_id):

    status_logger.info("Thread PM sensor: {} started".format(sensor_name))

    sensor_type = config.get_config(sensor_name)

    if sensor_type == "PMS5003":
        try:
            plantower = Plantower(pins=pins, id=serial_id)

            # wait for sensor to calibrate/stabilize
            plantower.read()
            time.sleep(3)
        except PlantowerException as e:
            status_logger.exception("Failed to read from sensor {}".format(sensor_name))
            blink_led(colour=0x770000, delay=0.5, count=1)

        # variables for sensor reading and computing averages
        last_timestamp = None
        sensor_readings_lst = []

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
                            lst_to_log = [last_timestamp] + [str(int(i)) for i in
                                                             mean_across_arrays(sensor_readings_lst)]
                            line_to_log = ','.join(lst_to_log)
                            sensor_logger.log_row(line_to_log)
                        # Set/reset global variables
                        last_timestamp = curr_timestamp
                        sensor_readings_lst = []
                    # Add the current reading to the list, which will be processed when the timestamp changes
                    sensor_readings_lst.append(sensor_reading)
            except PlantowerException as e:
                status_logger.exception("Failed to read from sensor {}".format(sensor_name))
                blink_led(colour=0x770000, delay=0.5, count=1)

    elif sensor_type == "SPS030":

        LOOP_DELAY_S = 1  # cannot poll new reading within one second

        while True:
            try:
                SPS030 = Sensirion(pins=pins, id=serial_id)  # automatically starts measurement
                break
            except SensirionException as e:
                status_logger.exception("Failed to read from sensor {}".format(sensor_name))
                blink_led(colour=0x770000, delay=0.5, count=1)
                time.sleep(LOOP_DELAY_S)

        time.sleep(3)  # wait for sensor to calibrate/stabilize

        try:
            while True:
                time.sleep(LOOP_DELAY_S)

                recv = SPS030.read()
                if recv:
                    recv_lst = str(recv).split(',')
                    curr_timestamp = recv_lst[0]
                    sensor_reading_float = [float(i) for i in recv_lst[1:]]
                    sensor_reading_round = [round(i) for i in sensor_reading_float]
                    lst_to_log = [curr_timestamp] + [str(i) for i in sensor_reading_round]
                    line_to_log = ','.join(lst_to_log)
                    sensor_logger.log_row(line_to_log)
        except SensirionException as e:
            status_logger.exception("Failed to read from sensor {}".format(sensor_name))
            blink_led(colour=0x770000, delay=0.5, count=1)
