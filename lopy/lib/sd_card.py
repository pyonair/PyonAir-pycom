from machine import SD
import os


class SDCard:
    def __init__(self):
        print("1")
        self.sd = SD()
        print("2")
        self.path_template = '/sd/{}'
        os.mount(self.sd, '/sd')
        print("3")

    def write_line(self, filename, line):
        with open(self.path_template.format(filename), 'w') as f:
            f.write(line + '\n')
