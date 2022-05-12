from machine import I2C

#TODO: Somewhere there is a check for the year, to see if it is sensible, find it and stop it throting a critical halt.
class RtcDS1307:
    def __init__(self):

        # Initialise i2c - bus no., type, baudrate, i2c pins
        self.i2c = I2C(0, I2C.MASTER, baudrate=400000, pins=('P9', 'P10'))

        self.DS1307_I2C_ADDRESS = 104

        # Day of week is not used, but needs to be set
        self.h_wkday = 0x01
        self.weekday_start = 1

        self.second = None
        self.minute = None
        self.hour = None
        self.dayOfMonth = None
        self.month = None
        self.year = None

    def _dec2bcd(self, value):
        """Convert decimal to binary coded decimal (BCD) format"""
        return (value // 10) << 4 | (value % 10)

    def _bcd2dec(self, value):
        """Convert binary coded decimal (BCD) format to decimal"""
        return ((value >> 4) * 10) + (value & 0x0F)

    def set_time(self, h_yr, h_mnth, h_day, h_hr, h_min, h_sec):
        #TODO: year is not correct, mask error?
        # second, minute, hour, day of week, day of month, month, year
        data = bytearray([h_sec, h_min, h_hr, self.h_wkday, h_day, h_mnth, h_yr])

        self.i2c.writeto(self.DS1307_I2C_ADDRESS, 0)
        self.i2c.writeto_mem(self.DS1307_I2C_ADDRESS, 0, data)

    def get_time(self):
        self.i2c.writeto(self.DS1307_I2C_ADDRESS, 0x00)
        data = self.i2c.readfrom_mem(self.DS1307_I2C_ADDRESS, 0x00, 0xFF)
        print(data)
        # Split date and time from RTC output[2:] removes 0x characters
        self.second = int(data[0] & 0x7F)
        self.minute = self._bcd2dec(data[1])
        self.hour = self._bcd2dec(data[2])  # Need to change this if 12 hour am/pm
        # Day of week is not used, but needs to be set
        self.h_wkday = self._bcd2dec(data[3] - self.weekday_start)
        self.dayOfMonth = self._bcd2dec(data[4])
        self.month = self._bcd2dec(data[5])
        self.year = self._bcd2dec(data[6]) + 2000


        datetime = (self.year, self.month, self.dayOfMonth, self.hour, self.minute, self.second, 0, 0)
        print(datetime)
        return datetime


clock = RtcDS1307()
