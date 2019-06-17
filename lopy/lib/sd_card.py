from machine import SD
import os
from strings import headers_dict_v3

headers = headers_dict_v3['PMS5003']


class SDCard:
    def __init__(self, sensor_logfile, status_logfile=None):
        self.sd = SD()
        self.path_template = '/sd/{}'
        os.mount(self.sd, '/sd')
        self.sensor_logfile = sensor_logfile
        self.status_logfile = status_logfile

    def create_sensor_log_file(self):
        sensor_logfile = self.sensor_logfile
        # If the file exists, skip creation
        if sensor_logfile in os.listdir('/sd'):
            # TODO: log status
            return
        with open(self.path_template.format(sensor_logfile), 'w') as f:  # TODO: Change permission to x in production
            f.write(', '.join(headers) + '\n')

    def log_sensor_line(self, line):
        with open(self.path_template.format(self.sensor_logfile), 'a') as f:
            f.write(line + '\r\n')

    # Setters
    def set_sensor_logfile(self, sensor_logfile):
        self.sensor_logfile = sensor_logfile

    def set_status_logfile(self, status_logfile):
        self.status_logfile = status_logfile
