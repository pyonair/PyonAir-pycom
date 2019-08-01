from PM_thread import pm_thread
from SensorLogger import SensorLogger
import strings as s
import _thread


def initialize_pm_sensor(sensor_name, pins, serial_id, status_logger):
    try:
        filename_current = s.file_name_temp.format(sensor_name, s.current_ext)

        # Initialise sensor logger
        PM_logger = SensorLogger(filename=filename_current, terminal_out=True)

        # Start PM sensor thread
        _thread.start_new_thread(pm_thread, (sensor_name, PM_logger, status_logger, pins, serial_id))

        status_logger.info("Sensor " + sensor_name + " initialized")
    except Exception as e:
        status_logger.exception("Failed to initialize sensor " + sensor_name)