timestamp_template = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"  # yyyy-mm-dd hh-mm-ss
sensor_logfile_template = "{:04d}-{:02d}-{:02d}.csv"  # yyyy-mm-dd

headers_dict_v3 = {
    "PMS5003": ["timestamp", "sensor_id", "pm10_cf1", "PM1", "pm25_cf1", "PM25", "pm100_cf1", "PM10", "gr03um", "gr05um", "gr10um", "gr25um", "gr50um", "gr100um", ""],
    "PMS7003": ["timestamp", "sensor_id", "pm10_cf1", "PM1", "pm25_cf1", "PM25", "pm100_cf1", "PM10", "gr03um", "gr05um", "gr10um", "gr25um", "gr50um", "gr100um", ""],
    "PMSA003": ["timestamp", "sensor_id", "pm10_cf1", "PM1", "pm25_cf1", "PM25", "pm100_cf1", "PM10", "gr03um", "gr05um", "gr10um", "gr25um", "gr50um", "gr100um",""],
    "OPCN2": ["timestamp", "sensor_id", "PM1", "PM25", "PM10", "Bin0", "Bin1", "Bin1MToF", "Bin2", "Bin3", "Bin3MToF", "Bin4", "Bin5", "Bin5MToF", "Bin6", "Bin7", "Bin7MToF", "Bin8", "Bin9", "Bin10", "Bin11", "Bin12", "Bin13", "Bin14", "Bin15", "SFR", "Checksum", "SamplingPeriod"],
    "HPMA115S0": ["timestamp", "sensor_id", "PM10", "PM25"],
    "AM2302": ["timestamp", "sensor_id", "humidity", "temperature"],
    "OPCR1": ["timestamp", "sensor_id", "PM1", "PM25", "PM10", "Bin0", "Bin1", "Bin1MToF", "Bin2", "Bin3", "Bin3MToF", "Bin4", "Bin5", "Bin5MToF", "Bin6", "Bin7", "Bin7MToF", "Bin8", "Bin9", "Bin10", "Bin11", "Bin12", "Bin13", "Bin14", "Bin15", "SFR", "Checksum", "SamplingPeriod", "Temperature", "Humidity"],
    "SPS030": ["timestamp", "sensor_id", "PM1", "PM25", "PM4", "PM10", "n05", "n1", "n25", "n4", "n10", "tps"],
    "SDS018": ["timestamp", "sensor_id", "PM10", "PM25"]
}

status_header = ['type', 'timestamp', 'message']

config_filename = 'config.txt'

PM1_processing = '/sd/PM1.csv.processing'
PM1_current = '/sd/PM1.csv.current'
PM2_processing = '/sd/PM2.csv.processing'
PM2_current = '/sd/PM2.csv.current'
