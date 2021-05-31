from machine import I2C


class RtcDS1307:
    def __init__(self):

        # Initialise i2c - bus no., type, baudrate, i2c pins
        self.i2c = I2C(0, I2C.MASTER, baudrate=400000, pins=('P9', 'P10'))

        self.DS1307_I2C_ADDRESS = 104

        # Day of week is not used, but needs to be set
        self.h_wkday = 0x01

        self.second = None
        self.minute = None
        self.hour = None
        self.dayOfMonth = None
        self.month = None
        self.year = None

    def set_time(self, h_yr, h_mnth, h_day, h_hr, h_min, h_sec):

        # second, minute, hour, day of week, day of month, month, year
        data = bytearray([h_sec, h_min, h_hr, self.h_wkday, h_day, h_mnth, h_yr])

        self.i2c.writeto(self.DS1307_I2C_ADDRESS, 0)
        self.i2c.writeto_mem(self.DS1307_I2C_ADDRESS, 0, data)

    def get_time(self):
        self.i2c.writeto(self.DS1307_I2C_ADDRESS, 0x00)
        data = self.i2c.readfrom_mem(self.DS1307_I2C_ADDRESS, 0x00, 0xFF)

        # Split date and time from RTC output[2:] removes 0x characters
        self.second = int(hex(data[0])[2:])
        self.minute = int(hex(data[1])[2:])
        self.hour = int(hex(data[2])[2:])  # Need to change this if 12 hour am/pm
        self.dayOfMonth = int(hex(data[4])[2:])
        self.month = int(hex(data[5])[2:])
        self.year = int(hex(data[6])[2:])

        datetime = (int('20' + str(self.year)), self.month, self.dayOfMonth, self.hour, self.minute, self.second, 0, 0)

        return datetime


clock = RtcDS1307()
