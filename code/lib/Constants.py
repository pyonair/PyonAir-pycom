TIME_ISO8601_FMT = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"
# yyyy-mm-ddThh-mm-ss  #https://en.wikipedia.org/wiki/ISO_8601

FILENAME_FMT = "{:04d}-{:02d}-{:02d}"  # yyyy-mm-ddThh-mm-ss  #https://en.wikipedia.org/wiki/ISO_8601

# Just filename not location/path
LOG_FILENAME = "PyonAir"
LOG_EXT = ".log"
# The name of the logger instance -- no need to change
DEFAULT_LOG_NAME = "Pyonair"


# Names in JSON file (config)
LOG_LEVEL_KEY = "logging_lvl"  # TODO : rename to something sensible
AVERAGES_PER_HOUR_INT_KEY = "averagesPerHour"  # averages are done at same time(e.g. on the our, min = once per hour)

PM_SENSOR_SAMPLING_RATE = 1  # How many seconds to wait to read the PM sensors
PM_SAMPLE_COUNT_FOR_AVERAGE = 30  # How many samples to take before doing an average?

# config_filename = 'Settings.cfg'
CONFIG_FILE_NAME = "Settings.json"  # JSON file with all PYON air setting s -- on flash but can be on SD so public
CONFIG_FILE_DIRECTORY = "/sd/" #Location of default config file
CONFIG_FILE_FULL_NAME = (
    CONFIG_FILE_DIRECTORY + CONFIG_FILE_NAME
)  # os.path does not exist, so string concat

RING_BUFFER_DIR = "/sd/"
RING_BUFFER_FILE = "buffer.obj"

# CONFIG_FILE_FULL_NAME =
DEBUG_CONFIG_FILE_NAME = "debug_config.json"
DEBUG_CONFIG_FILE_DIRECTORY = "/flash/"  # os.path does not exist, so string concat
DEBUG_CONFIG_FILE_FULL_NAME = DEBUG_CONFIG_FILE_DIRECTORY + DEBUG_CONFIG_FILE_NAME


# Str name of the config in the strings file?
DEFAULT_CONFIG = {
    "device_id": "Test",
    "device_name": "NewPyonAir",
    "password": "newpyonair",
    "region": "Europe",
    "device_eui": "DONOTUSE",
    "application_eui": "DONOTUSE",
    "app_key": "DONOTUSE",
    "SSID": "SSID",
    "fmt_version": "1",
    "wifi_password": "1",
    "TEMP": "SHT35",
    "PM1": "PMS5003",
    "code_version": "1",
    "PM2": "SPS030",
    "GPS": "ON",
    "PM1_id": "002",
    "PM2_id": "003",
    "TEMP_id": "001",
    "GPS_id": "004",
    "interval": 15,
    "TEMP_period": 30,
    "GPS_period": 0.1,
    "PM1_init": 10,
    "PM2_init": 10,
    "logging_lvl": "DEBUG",
    "lora_timeout": 20,
    "GPS_timeout": 20,
    "config_timeout": 10,
    "fair_access": 30,
    "air_time": 75,
    "message_count": 0,
    "transmission_date": 0,
    "LORA": "ON",
    "update": False,
    "port": 8000,
    "averagesPerHour": 60,
    "server": "10.15.40.51",
}

# ============================Strings=================

"""Code is implemented semi-modular using these strings. While it is fine to change most of these strings without any
complication, please only do so, if you have looked at the uses and are confident that you know what you are doing."""


# use PM25 -- for average
headers_dict_v4 = {
    "PMS5003": [
        "timestamp",
        "pm10_cf1",
        "PM1",
        "pm25_cf1",
        "PM25",
        "pm100_cf1",
        "PM10",
        "gr03um",
        "gr05um",
        "gr10um",
        "gr25um",
        "gr50um",
        "gr100um",
        "",
    ],
    "PMS7003": [
        "timestamp",
        "pm10_cf1",
        "PM1",
        "pm25_cf1",
        "PM25",
        "pm100_cf1",
        "PM10",
        "gr03um",
        "gr05um",
        "gr10um",
        "gr25um",
        "gr50um",
        "gr100um",
        "",
    ],
    "PMSA003": [
        "timestamp",
        "pm10_cf1",
        "PM1",
        "pm25_cf1",
        "PM25",
        "pm100_cf1",
        "PM10",
        "gr03um",
        "gr05um",
        "gr10um",
        "gr25um",
        "gr50um",
        "gr100um",
        "",
    ],
    "OPCN2": [
        "timestamp",
        "PM1",
        "PM25",
        "PM10",
        "Bin0",
        "Bin1",
        "Bin1MToF",
        "Bin2",
        "Bin3",
        "Bin3MToF",
        "Bin4",
        "Bin5",
        "Bin5MToF",
        "Bin6",
        "Bin7",
        "Bin7MToF",
        "Bin8",
        "Bin9",
        "Bin10",
        "Bin11",
        "Bin12",
        "Bin13",
        "Bin14",
        "Bin15",
        "SFR",
        "Checksum",
        "SamplingPeriod",
    ],
    "HPMA115S0": ["timestamp", "PM10", "PM25"],
    "OPCR1": [
        "timestamp",
        "PM1",
        "PM25",
        "PM10",
        "Bin0",
        "Bin1",
        "Bin1MToF",
        "Bin2",
        "Bin3",
        "Bin3MToF",
        "Bin4",
        "Bin5",
        "Bin5MToF",
        "Bin6",
        "Bin7",
        "Bin7MToF",
        "Bin8",
        "Bin9",
        "Bin10",
        "Bin11",
        "Bin12",
        "Bin13",
        "Bin14",
        "Bin15",
        "SFR",
        "Checksum",
        "SamplingPeriod",
        "Temperature",
        "Humidity",
    ],
    "SPS030": [
        "timestamp",
        "PM1",
        "PM25",
        "PM4",
        "PM10",
        "n05",
        "n1",
        "n25",
        "n4",
        "n10",
        "tps",
    ],
    "SDS018": ["timestamp", "PM10", "PM25"],
    "AM2302": ["timestamp", "humidity", "temperature"],
    "BME280": ["timestamp", "humidity", "temperature", "pressure"],
    "SHT35": ["timestamp", "temperature", "humidity"],
}

# headers from headers_dict_v4 to calculate averages in task.py and send over LoRaWAN
lora_sensor_headers = {
    "SHT35": ["temperature", "humidity"],
    "PMS5003": ["PM10", "PM25"],
    "SPS030": ["PM10", "PM25"],
}

status_header = ["type", "timestamp", "message"]


# default_configuration = {"device_id": "", "device_name": "NewPyonAir", "password": "newpyonair", "region": "Europe",
#                          "device_eui": "", "application_eui": "", "app_key": "", "SSID": "", "fmt_version": "",
#                          "wifi_password": "", "TEMP": "SHT35", "PM1": "PMS5003", "code_version": "",
#                          "PM2": "SPS030", "GPS": "OFF", "PM1_id": "002", "PM2_id": "003", "TEMP_id": "001",
#                          "GPS_id": "004", "interval": 15, "TEMP_period": 30, "GPS_period": 12, "PM1_init": 30,
#                          "PM2_init": 30, "logging_lvl": "Warning", "lora_timeout": 20, "GPS_timeout": 20,
#                          "config_timeout": 10, "fair_access": 30, "air_time": 75, "message_count": 0,
#                          "transmission_date": 0, "LORA": "ON", "update": False, "port": 8000,
#                          "server": "10.15.40.51"}

# Sensor names
PM1 = "PM1"
PM2 = "PM2"
TEMP = "TEMP"
GPS = "GPS"

# Directories in /sd/
current = "Current"
processing = "Processing" ## Should not use now we have welfords
archive = "Archive"
archive_averages = "Averages"

# File names
lora_file_name = "LoRa_Buffer"
# wifi_file_name = 'WiFi_Buffer'

# Paths
#TODO Constants as caps?
root_path = "/sd/"
current_path = root_path + current + "/"
processing_path = root_path + processing + "/"
archive_path = root_path + archive + "/"
archive_averages_path = archive_path + archive_averages + "/"
filesystem_dirs = [current, processing, archive]
