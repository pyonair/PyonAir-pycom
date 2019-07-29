from machine import I2C
import time


# Temp Res: 0.01C, Temp Acc: +/-0.1C, Humid Res: 0.01%, Humid Acc: +/-1.5%
class TempSHT35(object):

    def __init__(self):

        # Initialise i2c - bus no., type, baudrate, i2c pins
        self.i2c = I2C(0, I2C.MASTER, baudrate=9600, pins=('P9', 'P10'))

        self.address = 0x45

    def read(self):
        # high repeatability, clock stretching disabled
        self.i2c.writeto_mem(self.address, 0x24, 0x00)

        # measurement duration < 16 ms
        time.sleep(0.016)

        # read 6 bytes back
        # Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
        data = self.i2c.readfrom_mem(self.address, 0x00, 6)
        temperature = data[0] * 256 + data[1]
        celsius = -45 + (175 * temperature / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
        if data[2] != CRC(data[:2]):
            raise RuntimeError("temperature CRC mismatch")
        if data[5] != CRC(data[3:5]):
            raise RuntimeError("humidity CRC mismatch")
        return [celsius, humidity]


#  Cycling redundancy check
def CRC(data):
    crc = 0xff
    for s in data:
        crc ^= s
        for i in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc
