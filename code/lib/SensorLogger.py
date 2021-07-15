"""
Simple logger for logging sensor readings.
Replaces the functionality of the sensor logger that was previously produced by the LoggerFactory
"""
import sys
from helper import current_lock  #TODO: a what lock? why?
import strings as s
import time
from Constants import FILENAME_FMT

#DONT use logger class here it is inefficient and renames all files on rollover. 

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

        timeStr = FILENAME_FMT.format(*time.gmtime()) 
        #timeStr = timeStr.replace(" ", "") # Use datetime at boot for filename. 
        
        self.filename = s.current_path + sensor_name + "-"+ timeStr  + '.csv'
        self.terminal_out = terminal_out
        self.terminator = terminator
        self.sensor_name = sensor_name

    def log_row(self, row):
        #Side effect = new file every reboot, no automatic reload. 
        row_to_log = row + self.terminator
        if self.terminal_out:
            sys.stdout.write(self.filename + " : " + row_to_log)
        #with current_lock: #TODO this cant be right -- why lock as I only have one writer per file??   -- Looks related to averages         
        with open(self.filename, 'a') as f:    #TODO: ineffiecient, and SD may hate it, but least it persists data. Consider buffer?             
            f.write(row_to_log)
                
