from plantowerpycom import Plantower, PlantowerException
from sensirionpycom import Sensirion, SensirionException
from helper import mean_across_arrays, blink_led
from Configuration import Configuration
from machine import Timer
from SensorLogger import SensorLogger
import time
from WelfordAverage import WelfordAverage
from Constants import PM_SENSOR_SAMPELING_RATE , PM_SAMPLE_COUNT_FOR_AVERAGE

#This is important code, keep it fast are reliable. 
#Entry point for thread (method only not class) 
def pm_thread(sensor_name,config,  debugLogger, pins, serial_id):
    rdr = PMSensorReader(sensor_name,config,  debugLogger, pins, serial_id)


#Deal with one sesnor , called by thread -- so remember on diff threads
class PMSensorReader:
    def __init__(self,sensor_name,config,  debugLogger, pins, serial_id):
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

        #Welfords variables -- keep average of these 
        
        self.gr03umAverage = WelfordAverage(debugLogger)
        self.gr05umAverage = WelfordAverage(debugLogger)
        self.gr10umAverage = WelfordAverage(debugLogger)
        #averages = [gr03umAverage,gr05umAverage,gr10umAverage] # list to pass single param, and not dict for speed
        self.sampleCounter = 0


        self.sensor_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True) 
        self.averageLogger = SensorLogger(sensor_name=sensor_name+"Average", terminal_out=True)
        
        self.sensor_type = config.get_config(sensor_name)
        self.init_time = int(config.get_config(sensor_name + "_init"))

        init_count = 0
        if self.sensor_type == "PMS5003":
            # initialise sensor
            self.sensor = Plantower(pins=pins, id=serial_id)
            time.sleep(1)
            #TODO: why is this like this, why not sleep for init_time -- do i need to clear the serial buffer?
            # warm up time  - readings are not logged
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
                    self.sensor = Sensirion(retries=1, pins=pins, id=serial_id)  # automatically starts measurement
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


        #Use welford here : https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        #Average variables? -- pass them in
        #TODO: Hold on do the sensirion and plantower return the same strings????
        #processing_alarm = Timer.Alarm(process_readings, arg=(sensor_type, sensor, sampleCounter, averages, sensor_logger,  averageLogger ,debugLogger), s=PM_SENSOR_SAMPELING_RATE, periodic=True)

        debugLogger.debug("Starting repeating alarm/timer")
        self.__processing_alarm = Timer.Alarm(self.process_readings, PM_SENSOR_SAMPELING_RATE, periodic=True)

        #DO averaging here? -- timer
        # TOO heavy processing_averages = Timer.Alarm(process_averages, arg=(averages,averageLogger,debugLogger), s=10, periodic=True)


    def process_averages(self):
        try:

            #averages, averageLogger, debugLogger = args[0], args[1], args[2]

            gr03umCount, gr03umMean, gr03umVariance, gr03umSampleVariance = averages[0].getAverageAndReset()
            #gr05umCount, gr05umMean, gr05umVariance, gr05umSampleVariance = averages[1].getAverageAndReset()
            #gr10umCount, gr10umMean, gr10umVariance, gr10umSampleVariance = averages[2].getAverageAndReset()

            #log to file
            if(gr03umCount == gr03umCount == gr03umCount):

                averageLogger.log_row("".join([str(gr03umMean)])) # , "," ,str(gr05umMean) , "," ,str(gr10umMean), "," , str(gr10umCount)]))
            else: 
                averageLogger.log_row("".join([str(gr03umMean) , "," ,str(gr05umMean) , "," ,str(gr10umMean) , "," , str(gr03umCount) , "," , str(gr05umCount) , "," , str(gr10umCount)]))
            
            #add to transmit?
        except Exception as e:
            debugLogger.error("Calculate average failed.")
            debugLogger.info(e)
        
            blink_led((0x550000, 0.4, True))
    
        


    def process_readings(self,alarm):
        """
        Method to be evoked by a timed alarm, which reads and processes data from the PM sensor, and logs it to the sd card
        :param args: sensor_type, sensor, sensor_logger, debugLogger
        :type args: str, str, SensorLogger object, LoggerFactory object
        """

        #sensor_type, sensor,sampleCounter , averages, sensor_logger, averageLogger,debugLogger   = args[0], args[1], args[2], args[3] ,  args[4] ,  args[5] ,  args[6]   #TODO: this looks clunky and in need of a fix
        print("START")
        #Must run 1Hz !
        try:
            #print(self.sensor)
            recv = self.sensor.read()
            print ("HERE1111" )
            #print ("HERE1111" +  str(recv) )
            if recv:
                recv_lst = str(recv).split(',')
                print ("HERE")
                curr_timestamp = recv_lst[0]
                sensor_reading_float = [float(i) for i in recv_lst[1:]]
                sensor_reading_round = [round(i) for i in sensor_reading_float]  #TODO: this looks VERY processor intensive (remember 1hz here! x number of sensors)
                lst_to_log = [curr_timestamp] + [str(i) for i in sensor_reading_round] #TODO: check that round is sane here
                line_to_log = ','.join(lst_to_log)
                
                self.sensor_logger.log_row(line_to_log)
                
                ##attempt averaging
                #ROWS: "timestamp", "pm10_cf1", "PM1", "pm25_cf1", "PM25", "pm100_cf1", "PM10", "gr03um", "gr05um", "gr10um", "gr25um", "gr50um", "gr100um", ""
                #IN ORDER "gr03um", "gr05um", "gr10um"
                if (self.sampleCounter < PM_SAMPLE_COUNT_FOR_AVERAGE): #Keep adding data
                    self.gr03umAverage.update(sensor_reading_round[7])
                    self.gr05umAverage.update(sensor_reading_round[8])
                    self.gr10umAverage.update(sensor_reading_round[9])
                    self.sampleCounter += 1
                    print(self.sampleCounter)

                else:
                    self.sampleCounter = 0
                    gr03umCount, gr03umMean, gr03umVariance, gr03umSampleVariance = self.averages[0].getAverageAndReset()
                    gr05umCount, gr05umMean, gr05umVariance, gr05umSampleVariance = self.averages[1].getAverageAndReset()
                    gr10umCount, gr10umMean, gr10umVariance, gr10umSampleVariance = self.averages[2].getAverageAndReset()
                    if(gr03umCount == gr03umCount == gr03umCount):
                        self.averageLogger.log_row("".join([str(gr03umMean)])) # , "," ,str(gr05umMean) , "," ,str(gr10umMean), "," , str(gr10umCount)]))
                    else: 
                        self.averageLogger.log_row("".join([str(gr03umMean) , "," ,str(gr05umMean) , "," ,str(gr10umMean) , "," , str(gr03umCount) , "," , str(gr05umCount) , "," , str(gr10umCount)]))
                    


        except Exception as e:
            self.debugLogger.error("Failed to read from sensor {}".format(self.sensor_type))
            #debugLogger.debug(e)
        
            blink_led((0x550000, 0.4, True))
            #we can get serial issues, ignore and hope we fix as we go along
            pass
    

        