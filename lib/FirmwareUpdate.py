# Firmware update by reading the image from the SD card
# adapted from https://docs.pycom.io/firmwareapi/pycom/pycom/
from pycom import ota_start, ota_write, ota_finish
import os
from machine import SD
from LoggerFactory import LoggerFactory
from loggingpycom import DEBUG     
from micropython import const 
import machine
   
###
# Mount SD card
# sd = SD()
# os.mount(sd, '/sd')
# from FirmwareUpdate import FirmwareUpdate
# fw = FirmwareUpdate()
# fw.DoTheUpdate()
###
class FirmwareUpdate:
    def __init__(self, logger):
        self.BLOCKSIZE = const(4096)
        self.APPIMG = "/sd/update.bin"
        self.logger = logger        
        self.logger.info("Be careful this is a NON-standard update method")
        self.logger.info("You must mount SD storage")
        self.logger.info("You must check file exists")
        self.logger.info("--STOP NOW-- unless you know what you are doing")
        

    def DoTheUpdate(self):
        self.logger.info(str(os.uname()))
        self.__do_update_from_SD()
        self.logger.info(str(os.uname()))


    def __do_update_from_SD(self):
        
        
        self.logger.debug("Files: {}".format(os.listdir('/sd')))
        self.logger.debug("{}".format(str(os.stat(self.APPIMG))))
        with open(self.APPIMG, "rb") as f:
            buffer = bytearray(self.BLOCKSIZE)
            mv = memoryview(buffer)
            size=0
            self.logger.info("Start update...")
            file_size = os.stat(self.APPIMG)[6] #6th item
            ota_start()
            while True:
                chunk = f.readinto(buffer)
                if chunk > 0:
                    ota_write(mv[:chunk])
                    size += chunk
                    self.logger.info("{0} of {1}".format(size, file_size))
                else:
                    break
            self.logger.info("Finishing update...")
            ota_finish()
        #os.remove(self.APPIMG)  
        self.logger.info("Complete, rebooting...")  
        #machine.reset()

### Manual mode
# If you are realy stuck, put the bin file on the SD card
# Make sure it is the non pybytes firmware!
# Enter REPL mode https://docs.pycom.io/gettingstarted/programming/repl/
# Press ctrl + e to enter edit paste mode
# Paster the code below
# Ctrl + d to exit and execute
# WAIT!!!
# when done, reboot
###
'''
from pycom import ota_start, ota_write, ota_finish
from machine import SD
import os
sd = SD()
os.mount(sd, '/sd')
BLOCKSIZE = const(4096)
APPIMG = "/sd/update.bin"
print(os.uname())
with open(APPIMG, "rb") as f:
    buffer = bytearray(BLOCKSIZE)
    mv = memoryview(buffer)
    size=0
    file_size = os.stat(APPIMG)[6] #6th item
    ota_start()
    while True:
        chunk = f.readinto(buffer)
        if chunk > 0:
            ota_write(mv[:chunk])
            size += chunk
            print("{0} of {1}".format(size, file_size))
        else:
            break
    ota_finish()
'''