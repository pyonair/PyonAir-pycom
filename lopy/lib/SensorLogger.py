"""
Simple logger for logging sensor readings.
Replaces the functionality of the sensor logger that was previously produced by the LoggerFactory
"""
import sys

class SensorLogger:
    def __init__(self, filename, terminal_out=True, terminator='\n'):
        """
        :param filename: name of the out log file
        :type filename: str
        :param terminal_out: print output to terminal
        :type terminal_out: bool
        :param terminator: end of line character
        :type terminator: object
        """
        self.filename = filename
        self.terminal_out = terminal_out
        self.terminator = terminator

    def log_row(self, row):
        row_to_log = row + self.terminator
        if self.terminal_out:
            sys.stdout.write(row_to_log)
        with open(self.filename, 'a') as f:
            f.write(row_to_log)