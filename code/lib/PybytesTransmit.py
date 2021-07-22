from helper import mean_across_arrays, blink_led
from Configuration import Configuration
from machine import Timer , temperature
import time
from Constants import * 
import struct
#PYBYTES
import pycom
from _pybytes import Pybytes
from _pybytes_config import PybytesConfig
from ubinascii import hexlify


# Message structures: (first CSV in string is type, must match below. rest is message)

#"TPP": s.TPP, "TP": s.TP, "PP": s.PP, "P": s.P, "T": s.T, "G": s.G}
# Format	C Type	Python	Notes
# x	pad byte	no value	 
# c	char	string of length 1	 
# b	signed char	integer	 
# B	unsigned char	integer	 
# ?	_Bool	bool	
# h	short	integer	 
# H	unsigned short	integer	 
# i	int	integer	 
# I	unsigned int	integer or long	 
# l	long	integer	 
# L	unsigned long	long	 
# q	long long	long	
# Q	unsigned long long	long	
# f	float	float	 
# d	double	float	 
# s	char[]	string	 
# p	char[]	string	 
# P	void *	long	 





### PORT, STRUCTURE_STRING
_messageFormats = {
# TEMP, PM1, PM2
# fmt_version-B / timestamp-H / TEMP_id-H / temperature-h / humidity-h / TEMP_count-H /
# / PM1_id-H / PM1_PM10-B / PM1_PM25-B / PM1_count-H / PM2_id-H / PM2_ PM10-B / PM2_PM25-B / PM2_count-H
"TPP" : [1, '<BHHhhHHBBHHBBH'],

# TEMP, PM
# fmt_version-B / timestamp-H / TEMP_id-H / temperature-h / humidity-h / TEMP_count-H /
# / PM1_id-H / PM1_PM10-B / PM1_PM25-B / PM1_count-H
"TP": [2,'<BHHhhHHBBH'] ,

# PM1, PM2
# fmt_version-B / timestamp-H / PM1_id-H / PM1_PM10-B / PM1_PM25-B / PM1_count-H / PM2_id-H / PM2_ PM10-B / PM2_PM25-B /
# PM2_count-H
"PP" : [3,  '<BHHBBHHBBH'],

# PM
# fmt_version-B / timestamp-H / PM1_id-H / PM1_PM10-B / PM1_PM25-B / PM1_count-H
"P" : [4, '<BHHBBH'],

# TEMP
# fmt_version-B / timestamp-H / TEMP_id-H / temperature-h / humidity-h / TEMP_count-H
"T" :[5,  '<BHHhhH'],

# GPS
# fmt_version-B / timestamp-H / GPS_id-H / lat-f / long-f / alt-f
"G" : [6,  '<BHHfff'],

# eg: 2021-07-21 12:10:25,A,1,10,917.5,1035.167,931.6499
# fmt_version-Byte / timestamp-H / str(self.welfordsCount) /,str(self.welfordsMean) /,str(sampleVariance)/ str(variance)])
"A": [7, '<BHHHH']
}



#This is important code, keep it FAST are reliable. 
#Note syntax issues here may look like cannot read sensors
#Entry point for thread (method only not class) 
def pybytes_thread(msgBuffer, config,  debugLogger):
    #Thread creates object and keeps it always.-- object triggers alarms. -- one per PM sensor
    bfr = PyBytesSender(msgBuffer, config,  debugLogger)
    bfr.processMessageBuffer()


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
        pybytes.start(autoconnect=True)  #same as connect method
        while not pybytes.isconnected():
            time.sleep(2)
            print(".")
            pybytes.start(autoconnect=True)

        self.debugLogger.info("Pybytes sender setup...")
        pybytes.print_config()
        #pybytes.send_info_message()
        pybytes.send_ping_message()
        #pdb.set_trace()
         
def processMessageBuffer(self):
        while True:
            try:
                #pybytes.send_signal(1, 0) # Sort of similar to uptime, sent to note reboot
                #self.debugLogger.info(str(pybytes.isconnected()))
                time.sleep(20)
                self.debugLogger.info("Memory:  " + str(pycom.get_free_heap()) + " Temp: " + str((temperature() - 32) / 1.8))

                #get a data packet

                msg = self.msgBuffer.pop()
                buffer_lst = msg.split(',')  # convert string to a list of strings
                #print(buffer_lst)
                # get structure and port from format
                timeStr = buffer_lst[2]
                fmt = buffer_lst[0]  # format is first item in the list
                msgVersion = buffer_lst[1] 
                lst_message = buffer_lst[2:]  #  chop year, month and format   
                
                msgType = _messageFormats[fmt]  # get dictionary corresponding to the format
                port = msgType[0]# get port corresponding to the format
                structure = msgType[1] # get structure corresponding to the format
                #print(str(structure))
                #print(lst_message)
                # cast message according to format to form valid payload
                
                cast_lst_message = []
                for i in range((len(structure) - 1)):  # iterate for length of structure having '<' stripped
                    #print(str(structure[i + 1]))
                    if structure[i + 1] == 'f':  # iterate through structure ignoring '<'
                        cast_lst_message.append(float(lst_message[i]))  # cast to float if structure is 'f'
                        #print("here222222")
                    else:
                        cast_lst_message.append(int(lst_message[i]))  # cast to int otherwise
                        #print("hwere33333")

                # pack payload
                self.debugLogger.debug("Sending over LoRa: " + str(cast_lst_message))
                #payload = struct.pack(structure, *cast_lst_message)  # define payload with given structure and list of averages
                #print( hexlify(payload))
                #TODO: message time stamp is missing!
                #print("here1111")
                #pybytes.send_signal(port, str(payload)) # Sort of similar to uptime, sent to note reboot
                #pybytes.send_signal(port, str(hexlify(payload)))# cast_lst_message) #25 bytes???
                pybytes.send_signal(port, cast_lst_message) 

                
            except Exception as e:
                print(str(e))
                print ("Carry on....")




## thread pybytes and attempt to send data from buffer