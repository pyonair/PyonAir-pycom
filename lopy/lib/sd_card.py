from machine import SD
import os
from strings import headers_dict_v3

headers = headers_dict_v3['PMS5003']


class SDCard:
    def __init__(self):
        self.sd = SD()
        self.path_template = '/sd/{}'
        os.mount(self.sd, '/sd')

    def create_log_file(self, filename):
        with open(self.path_template.format(filename), 'w') as f:  # TODO: Change permission to x in production
            f.write(', '.join(headers) + '\n')

    def write_line(self, filename, line):
        with open(self.path_template.format(filename), 'a') as f:
            f.write(line + '\r\n')
