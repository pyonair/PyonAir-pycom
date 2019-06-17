from machine import SD
import os
from strings import headers_dict_v3, status_header, timestamp_template

sensor_header = headers_dict_v3['PMS5003']


class SDCard:
    def __init__(self, rtc, sensor_logfile, status_logfile, debug=False):
        """
        :param rtc: initialised instance of the RTC class from the machine library
        :param sensor_logfile: filename for logging the sensor readings
        :param status_logfile: filename for logging the status messages
        :param debug: if True, prints status messages on the screen
        """
        self.rtc = rtc
        self.sensor_logfile = sensor_logfile
        self.status_logfile = status_logfile
        self.debug = debug

        self.path_template = '/sd/{}'
        self.sd = SD()

        # Status types
        self.INFO = 'INFO'
        self.WARN = 'WARN'
        self.ERROR = 'ERROR'

        # Run initialization routine
        self.initialize()

    def log_sensor_line(self, line):
        self.log_line_in_path(self.sensor_logfile, line)

    def log_status(self, msg_type, msg):
        """
        :param msg_type: type of status (defined in the __init__ of this class, e.g. SDCard.INFO)
        :param msg: message to be logged
        """
        line = '\t'.join([msg_type, timestamp_template.format(*self.rtc.now()), msg])
        if self.debug:
            print(line)
        self.log_line_in_path(self.status_logfile, line)

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

    ### Helper methods ###
    def create_logfile(self, filename, header, separator):
        """
        :param filename:
        :param header: list of strings containing the names of the headers (first line in the log file)
        :param separator: string separating the fields in the header (e.g. ', ')
        """
        # If the file exists, skip creation
        if filename in os.listdir('/sd'):
            self.log_status(self.INFO, '{} already exists, skipping its creation'.format(filename))
            return
        with open(self.path_template.format(filename), 'w') as f:
            f.write(separator.join(header) + '\n')

    def log_line_in_path(self, filename, line):
        with open(self.path_template.format(filename), 'a') as f:
            f.write(line + '\r\n')