"""
Simple logger for logging sensor readings.
Replaces the functionality of the sensor logger that was previously produced by the LoggerFactory
"""
import sys
from helper import current_lock
import strings as s


class SensorLogger:
    def __init__(self, sensor_name, terminal_out=True, terminator='\n'):
        """
        :param sensor_name: sensor name
        :type sensor_name: str
        :param terminal_out: print output to terminal
        :type terminal_out: bool
        :param terminator: end of line character
        :type terminator: object
        """
        self.filename = s.current_path + sensor_name + '.csv'
        self.terminal_out = terminal_out
        self.terminator = terminator
        self.sensor_name = sensor_name

    def log_row(self, row):
        row_to_log = row + self.terminator
        if self.terminal_out:
            sys.stdout.write(self.sensor_name + " - " + row_to_log)
        with current_lock:
            with open(self.filename, 'a') as f:
                f.write(row_to_log)
