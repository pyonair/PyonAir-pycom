from plantowerpycom import Plantower, PlantowerException
from sensirionpycom import Sensirion, SensirionException
from helper import mean_across_arrays, blink_led
from Configuration import Configuration
from machine import Timer
from SensorLogger import SensorLogger
import time


def pm_thread(sensor_name,config,  status_logger, pins, serial_id):
    """
    Method to run as a thread that reads, processes and logs readings form pm sensors according to their type
    :param sensor_name: PM1 or PM2
    :type sensor_name: str
    :param status_logger: status logger
    :type status_logger: LoggerFactory object
    :param pins: serial bus pins (TX, RX)
    :type pins: tuple(int, int)
    :param serial_id: serial bus id (0, 1 or 2)
    :type serial_id: int
    """

    status_logger.debug("Thread {} started".format(sensor_name))

    sensor_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True) #TODO: check this is not made every loop
    config = config
    sensor_type = config.get_config(sensor_name)
    init_time = int(config.get_config(sensor_name + "_init"))

    init_count = 0

    if sensor_type == "PMS5003":

        # initialise sensor
        sensor = Plantower(pins=pins, id=serial_id)

        time.sleep(1)
        #TODO: why is this like this, why not sleep for init_time -- do i need to clear the serial buffer?
        # warm up time  - readings are not logged
        while init_count < init_time:
            try:
                time.sleep(1)
                sensor.read()
                init_count += 1
            except PlantowerException as e:
                status_logger.exception("Warming up PMS5003")
                blink_led((0x550000, 0.4, True))

    elif sensor_type == "SPS030":

        # initialise sensor
        while True:
            try:
                sensor = Sensirion(retries=1, pins=pins, id=serial_id)  # automatically starts measurement
                break
            except SensirionException as e:
                status_logger.exception("Warming up SPS030")
                blink_led((0x550000, 0.4, True))
                time.sleep(1)

        # warm up time  - readings are not logged
        while init_count < init_time:
            try:
                time.sleep(1)
                sensor.read()
                init_count += 1
            except SensirionException as e:
                status_logger.exception("Failed to read from sensor SPS030")
                blink_led((0x550000, 0.4, True))

    # start a periodic timer interrupt to poll readings every second
    processing_alarm = Timer.Alarm(process_readings, arg=(sensor_type, sensor, sensor_logger, status_logger), s=1, periodic=True)


def process_readings(args):
    """
    Method to be evoked by a timed alarm, which reads and processes data from the PM sensor, and logs it to the sd card
    :param args: sensor_type, sensor, sensor_logger, status_logger
    :type args: str, str, SensorLogger object, LoggerFactory object
    """

    sensor_type, sensor, sensor_logger, status_logger = args[0], args[1], args[2], args[3]

    try:
        recv = sensor.read()
        if recv:
            recv_lst = str(recv).split(',')
            curr_timestamp = recv_lst[0]
            sensor_reading_float = [float(i) for i in recv_lst[1:]]
            sensor_reading_round = [round(i) for i in sensor_reading_float]
            lst_to_log = [curr_timestamp] + [str(i) for i in sensor_reading_round]
            line_to_log = ','.join(lst_to_log)
            sensor_logger.log_row(line_to_log)
    except Exception as e:
        status_logger.error("Failed to read from sensor {}".format(sensor_type))
        blink_led((0x550000, 0.4, True))
