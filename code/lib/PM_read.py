from plantowerpycom import Plantower, PlantowerException
from sensirionpycom import Sensirion, SensirionException
from helper import mean_across_arrays, blink_led
from Configuration import Configuration
from machine import Timer
from SensorLogger import SensorLogger
import time
from WelfordAverage import WelfordAverage

#This important code, keep it fast are reliable. 

def pm_thread(sensor_name,config,  debugLogger, pins, serial_id):
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

    debugLogger.debug("Thread {} started".format(sensor_name))

    #Welfords variables -- keep average of these 
    
    gr03umAverage = WelfordAverage(debugLogger)
    gr05umAverage = WelfordAverage(debugLogger)
    gr10umAverage = WelfordAverage(debugLogger)
    averages = [gr03umAverage,gr05umAverage,gr10umAverage] # list to pass single param, and not dict for speed


    sensor_logger = SensorLogger(sensor_name=sensor_name, terminal_out=True) 
    averageLogger = SensorLogger(sensor_name=sensor_name+"Average", terminal_out=True)
    
    sensor_type = config.get_config(sensor_name)
    init_time = int(config.get_config(sensor_name + "_init"))

    init_count = 0

    if sensor_type == "PMS5003":

        # initialise sensor
        sensor = Plantower(pins=pins, id=serial_id)

        time.sleep(1)
        #TODO: why is this like this, why not sleep for init_time -- do i need to clear the serial buffer?
        # warm up time  - readings are not logged
        while init_count < init_time:
            try:
                time.sleep(1)
                sensor.read()
                init_count += 1
            except PlantowerException as e:
                debugLogger.exception("Error warming up PMS5003")
                blink_led((0x550000, 0.4, True))

    elif sensor_type == "SPS030":

        # initialise sensor
        while True:
            try:
                sensor = Sensirion(retries=1, pins=pins, id=serial_id)  # automatically starts measurement
                break
            except SensirionException as e:
                debugLogger.exception("Error warming up SPS030")
                blink_led((0x550000, 0.4, True))
                time.sleep(1)

        # warm up time  - readings are not logged
        while init_count < init_time:
            try:
                time.sleep(1)
                sensor.read()
                init_count += 1
            except SensirionException as e:
                debugLogger.exception("Failed to read from sensor SPS030")
                blink_led((0x550000, 0.4, True))

    # start a periodic timer interrupt to poll readings every second


    #Use welford here : https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
    #Average variables? -- pass them in
    #TODO: Hold on do the sensirion and plantower return the same strings????
    processing_alarm = Timer.Alarm(process_readings, arg=(sensor_type, sensor, sensor_logger, debugLogger,averages), s=1, periodic=True)

    #DO averaging here? -- timer
    processing_averages = Timer.Alarm(process_averages, arg=(averages,averageLogger), s=10, periodic=True)


def process_averages(args):
    averages, averageLogger  = args[0], args[1]

    gr03umCount, gr03umMean, gr03umVariance, gr03umSampleVariance = averages[0].getAverageAndReset()
    gr05umCount, gr05umMean, gr05umVariance, gr05umSampleVariance = averages[1].getAverageAndReset()
    gr10umCount, gr10umMean, gr10umVariance, gr10umSampleVariance = averages[2].getAverageAndReset()

    #log to file
    if(gr03umCount == gr03umCount == gr03umCount):

        averageLogger.log_row("".join([str(gr03umMean) , "," ,str(gr05umMean) , "," ,str(gr10umMean), "," , str(gr10umCount)]))
    else: 
        averageLogger.log_row("".join([str(gr03umMean) , "," ,str(gr05umMean) , "," ,str(gr10umMean) , "," , str(gr03umCount) , "," , str(gr05umCount) , "," , str(gr10umCount)]))
    
    #add to transmit?

    


def process_readings(args):
    """
    Method to be evoked by a timed alarm, which reads and processes data from the PM sensor, and logs it to the sd card
    :param args: sensor_type, sensor, sensor_logger, debugLogger
    :type args: str, str, SensorLogger object, LoggerFactory object
    """

    sensor_type, sensor, sensor_logger, debugLogger, averages   = args[0], args[1], args[2], args[3] ,  args[4]   #TODO: this looks clunky and in need of a fix

    try:
        recv = sensor.read()
        if recv:
            recv_lst = str(recv).split(',')
            curr_timestamp = recv_lst[0]
            sensor_reading_float = [float(i) for i in recv_lst[1:]]
            sensor_reading_round = [round(i) for i in sensor_reading_float]  #TODO: this looks VERY processor intensive (remember 1hz here! x number of sensors)
            lst_to_log = [curr_timestamp] + [str(i) for i in sensor_reading_round] #TODO: check that round is sane here
            line_to_log = ','.join(lst_to_log)
            
            sensor_logger.log_row(line_to_log)
            

            ##attempt averaging
            #ROWS: "timestamp", "pm10_cf1", "PM1", "pm25_cf1", "PM25", "pm100_cf1", "PM10", "gr03um", "gr05um", "gr10um", "gr25um", "gr50um", "gr100um", ""
            #IN ORDER "gr03um", "gr05um", "gr10um"
            averages[0].update(sensor_reading_round[7])
            averages[1].update(sensor_reading_round[8])
            averages[2].update(sensor_reading_round[9])

    except Exception as e:
        debugLogger.error("Failed to read from sensor {}".format(sensor_type))
        debugLogger.info(e)
    
        blink_led((0x550000, 0.4, True))
 

    