from machine import SD
import os


class SDCard:
    def __init__(self):
        self.sd = SD()
        self.path_template = '/sd/{}'
        os.mount(self.sd, '/sd')

    def write_line(self, filename, line):
        with open(self.path_template.format(filename), 'w') as f:
            f.write(line + '\n')
