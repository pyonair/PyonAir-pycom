from machine import SD
import os
from strings import headers_dict_v3, status_header

sensor_header = headers_dict_v3['PMS5003']


class SDCard:
    def __init__(self, rtc, sensor_logfile, status_logfile):
        """
        :param rtc: initialised instance of the RTC class from the machine library
        :param sensor_logfile: filename for logging the sensor readings
        :param status_logfile: filename for logging the status messages
        """
        self.rtc = rtc
        self.sd = SD()
        self.path_template = '/sd/{}'
        self.sensor_logfile = sensor_logfile
        self.status_logfile = status_logfile

        # Status types
        self.INFO = 'INFO'
        self.WARN = 'WARN'
        self.ERROR = 'ERROR'

        # Run initialization routine
        self.initialize()

    def log_sensor_line(self, line):
        with open(self.path_template.format(self.sensor_logfile), 'a') as f:
            f.write(line + '\r\n')

    def log_status(self, msg_type, debug):
        """
        :param msg_type: type of status (defined in the __init__ of this class, e.g. SDCard.INFO)
        :param debug: if True, prints status messages on the screen
        :type debug: bool
        """

    def initialize(self):
        # Mount SD card
        os.mount(self.sd, '/sd')
        # Create log files
        self.create_logfile(self.sensor_logfile, sensor_header, ', ')
        self.create_logfile(self.status_logfile, status_header, '\t')

    # Setters
    def set_sensor_logfile(self, sensor_logfile):
        self.sensor_logfile = sensor_logfile

    def set_status_logfile(self, status_logfile):
        self.status_logfile = status_logfile

    # Helper methods
    def create_logfile(self, filename, header, separator):
        """
        :param filename:
        :param header: list of strings containing the names of the headers (first line in the log file)
        :param separator: string separating the fields in the header (e.g. ', ')
        """
        # If the file exists, skip creation
        if filename in os.listdir('/sd'):
            # TODO: log status
            return
        with open(self.path_template.format(filename), 'w') as f:
            f.write(separator.join(header) + '\n')
