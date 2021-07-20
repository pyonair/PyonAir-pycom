from helper import mean_across_arrays, blink_led
from Configuration import Configuration
from machine import Timer
import time
from Constants import * 
#PYBYTES
import pycom
from _pybytes import Pybytes
from _pybytes_config import PybytesConfig

#This is important code, keep it FAST are reliable. 
#Note syntax issues here may look like cannot read sensors
#Entry point for thread (method only not class) 
def pybytes_thread(msgBuffer, config,  debugLogger):
    #Thread creates object and keeps it always.-- object triggers alarms. -- one per PM sensor
    bfr = PyBytesSender(msgBuffer, config,  debugLogger)


#Deal with one sesnor , called by thread -- so remember on diff threads
class PyBytesSender:
    def __init__(self,msgBuffer, config,  debugLogger):
        self.msgBuffer = msgBuffer
        self.config = config
        self.debugLogger = debugLogger
        #========Pybytes
        pycom.nvs_set('pybytes_debug',99 ) #0 warning - 99 all
        pycom.pybytes_on_boot(False)

        conf = PybytesConfig().read_config()
        pybytes = Pybytes(conf)
        #backup config
        #naw.... pybytes.write_config([file=’/flash/pybytes_config.json’, silent=False])

        pybytes.update_config('pybytes_autostart', False, permanent=True, silent=False, reconnect=False)

        while not pybytes.isconnected():
            time.sleep(2)
            print(".")
        self.debugLogger.warning("Update")
        #pdb.set_trace()
         
        pybytes.start(autoconnect=True)  #same as connect method

        pybytes.send_signal(1, 0) # Sort of similar to uptime, sent to note reboot

        self.debugLogger.warning("Pybytes config done")




## thread pybytes and attempt to send data from buffer