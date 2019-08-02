from PM_thread import pm_thread
from SensorLogger import SensorLogger
import _thread
import strings as s
import os


def initialize_pm_sensor(sensor_name, pins, serial_id, status_logger):
    try:
        # Initialise sensor logger
        PM_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True)

        # Start PM sensor thread
        _thread.start_new_thread(pm_thread, (sensor_name, PM_logger, status_logger, pins, serial_id))

        status_logger.info("Sensor " + sensor_name + " initialized")
    except Exception as e:
        status_logger.exception("Failed to initialize sensor " + sensor_name)


def initialize_file_system():
    """
    Create directories for logging, processing, and sending data if they do not exist.
    """
    for directory in s.filesystem_dirs:
        if directory not in os.listdir(s.root_path):
            os.mkdir(s.root_path + directory)


def remove_residual_files():
    """
    Removes residual files from the last boot in the current and processing dirs
    """
    for path in [s.current_path, s.processing_path]:
        for file in os.listdir(path):
            os.remove(path + file)