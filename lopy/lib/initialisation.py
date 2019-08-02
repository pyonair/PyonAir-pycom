from PM_thread import pm_thread
from SensorLogger import SensorLogger
import _thread


def initialize_pm_sensor(sensor_name, pins, serial_id, status_logger):
    try:
        # Initialise sensor logger
        PM_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True)

        # Start PM sensor thread
        _thread.start_new_thread(pm_thread, (sensor_name, PM_logger, status_logger, pins, serial_id))

        status_logger.info("Sensor " + sensor_name + " initialized")
    except Exception as e:
        status_logger.exception("Failed to initialize sensor " + sensor_name)