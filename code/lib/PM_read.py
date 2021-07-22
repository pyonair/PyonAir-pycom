from plantowerpycom import Plantower, PlantowerException
from sensirionpycom import Sensirion, SensirionException
from helper import mean_across_arrays, blink_led,minutes_of_the_month
from Configuration import Configuration
from machine import Timer
from SensorLogger import SensorLogger
import time
from WelfordAverage import WelfordAverage
from Constants import PM_SENSOR_SAMPELING_RATE , PM_SAMPLE_COUNT_FOR_AVERAGE, TIME_ISO8601_FMT

#This is important code, keep it FAST are reliable. 
#Note syntax issues here may look like cannot read sensors
#Entry point for thread (method only not class) 
def pm_thread(sensor_name,msgBuffer, config,  debugLogger, pins, serial_id):
    #Thread creates object and keeps it always.-- object triggers alarms. -- one per PM sensor
    rdr = PMSensorReader(sensor_name,msgBuffer, config,  debugLogger, pins, serial_id)


#Deal with one sesnor , called by thread -- so remember on diff threads
class PMSensorReader:
    def __init__(self,sensor_name, msgBuffer, config,  debugLogger, pins, serial_id):
        """
        Method to run as a thread that reads, processes and logs readings form pm sensors according to their type
        :param sensor_name: PM1 or PM2
        :type sensor_name: str
        :param debugLogger: status logger
        :type debugLogger: LoggerFactory object
        :param pins: serial bus pins (TX, RX)
        :type pins: tuple(int, int)
        :param serial_id: serial bus id (0, 1 or 2)
        :type serial_id: int
        """
        self.debugLogger = debugLogger
        self.sensor_name = sensor_name
        self.debugLogger.debug("Thread {} started".format(sensor_name))
        self.msgBuffer = msgBuffer
        
        #Welford is now inline and not an object to save memory. 
        #Use welford here : https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        self.welfordsCount = 0
        self.welfordsMean = 0
        self.welfordsM2 = 0        

        #Logging files (sensor data and average senor data)
        self.sensor_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True) 
        self.averageLogger = SensorLogger(sensor_name=sensor_name+"Average", terminal_out=True)
        
        # Name PM1 - > Plantower via config.
        self.sensor_type = config.get_config(sensor_name)
        # Wait for sensor to poer up time from config
        self.init_time = int(config.get_config(sensor_name + "_init"))

        init_count = 0
        if self.sensor_type == "PMS5003":
            # initialise sensor
            self.sensor = Plantower(pins=pins, id=serial_id)  #TODO pass in logger to this sub lib?
            time.sleep(1)
            
            while init_count < self.init_time:
                try:
                    time.sleep(1)
                    self.sensor.read()
                    init_count += 1
                except PlantowerException as e:
                    debugLogger.exception("Error warming up PMS5003")
                    blink_led((0x550000, 0.4, True))

        elif self.sensor_type == "SPS030":

            # initialise sensor
            while True:
                try:
                    self.sensor = Sensirion(retries=1, pins=pins, id=serial_id)  # automatically starts measurement? #TODO pass in logger to this sub lib?
                    break
                except SensirionException as e:
                    self.debugLogger.exception("Error warming up SPS030")
                    blink_led((0x550000, 0.4, True))
                    time.sleep(1)

            # warm up time  - readings are not logged
            while init_count < self.init_time:
                try:
                    time.sleep(1)
                    self.sensor.read()
                    init_count += 1
                except SensirionException as e:
                    self.debugLogger.exception("Failed to read from sensor SPS030")
                    blink_led((0x550000, 0.4, True))

        # start a periodic timer interrupt to poll readings every second
        debugLogger.debug("Starting repeating alarm/timer")
        self.__processing_alarm = Timer.Alarm(self.process_readings, PM_SENSOR_SAMPELING_RATE, periodic=True)

    def process_readings(self,alarm):
        """
        Method to be evoked by a timed alarm, which reads and processes data from the PM sensor, and logs it to the sd card
        :param args: sensor_type, sensor, sensor_logger, debugLogger
        :type args: str, str, SensorLogger object, LoggerFactory object
        """
        
        #Must run 1Hz !
        try:
            recv = self.sensor.read() #This string should be fine to just log, but we do need some values to average
            if recv:
                revStr = str(recv) 
                recvList = revStr.split(',')
                
                self.sensor_logger.log_row(revStr)
                
                #==============Single welfords average=========
                #Average gr03umAverage = float(recvList[8])
                grumValue = float(recvList[8])  ## Value to average (we only average one)
                self.welfordsCount += 1 #increment N counter
                delta = float(grumValue) - self.welfordsMean
                self.welfordsMean += (delta/self.welfordsCount)
                delta2 = float(grumValue) - self.welfordsMean
                self.welfordsM2 += ( delta * delta2)
                #====End welfords==============

                if (self.welfordsCount >= PM_SAMPLE_COUNT_FOR_AVERAGE): #Keep adding data

                    variance = self.welfordsM2/self.welfordsCount
                    sampleVariance = self.welfordsM2 / (self.welfordsCount -1)  
                    #A = message type class/ see ring buffer -- for pickle    
                    curTime = minutes = str(minutes_of_the_month()) # TIME_ISO8601_FMT.format(*time.gmtime())                                
                    averageStr = ",".join(["A,1", curTime,  str(self.welfordsCount)  ,str(round(self.welfordsMean)) ,str(round(sampleVariance)),  str(round(variance))])
                    self.averageLogger.log_row(averageStr)

                    #self.msgBuffer.write(averageStr)  #TODO: add to buffer to Transmit this data
                    #Reset welfords
                    self.welfordsCount = 0
                    self.welfordsMean = 0
                    self.welfordsM2 = 0
            # #get an idea of time 0.0827
        except Exception as e:
            self.debugLogger.error("Failed to read from sensor {}".format(self.sensor_type))
            self.debugLogger.debug(str(e))
        
            #blink_led((0x550000, 0.4, True))
            #we can get serial issues, ignore and hope we fix as we go along
            pass
    

        