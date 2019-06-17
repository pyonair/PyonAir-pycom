from machine import SD
import os
from strings import headers_dict_v3

headers = headers_dict_v3['PMS5003']


class SDCard:
    def __init__(self, logfile, error_logfile=None):
        self.sd = SD()
        self.path_template = '/sd/{}'
        os.mount(self.sd, '/sd')
        self.logfile = logfile
        self.error_logfile = error_logfile

    def create_log_file(self, filename):
        with open(self.path_template.format(filename), 'w') as f:  # TODO: Change permission to x in production
            f.write(', '.join(headers) + '\n')

    def log_line(self, line):
        with open(self.path_template.format(self.logfile), 'a') as f:
            f.write(line + '\r\n')

    # Setters
    def set_logfile(self, logfile):
        self.logfile = logfile

    def set_error_logfile(self, error_logfile):
        self.error_logfile = error_logfile
