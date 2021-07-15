

##Move all constants here. 

#Just filename not location/path
LOG_FILENAME="PyonAir.log"
#The name of the logger instance -- no need to change
DEFAULT_LOG_NAME="Pyonair"


#Names in JSON file (config)
LOG_LEVEL_KEY= "logging_lvl" #TODO : rename to something sensible
AVERAGES_PER_HOUR_INT_KEY = "averagesPerHour" #averages are done at same time(e.g. on the our, min = once per hour)



#config_filename = 'Settings.cfg'
CONFIG_FILE_NAME = "Settings.json" # JSON file with all PYON air setting s -- on flash but can be on SD so public
CONFIG_FILE_DIRECTORY = "/sd/"
CONFIG_FILE_FULL_NAME = CONFIG_FILE_DIRECTORY + CONFIG_FILE_NAME #os.path does not exist, so string concat

#CONFIG_FILE_FULL_NAME = 
DEBUG_CONFIG_FILE_NAME = "debug_config.json"
DEBUG_CONFIG_FILE_DIRECTORY = "/flash/"  #os.path does not exist, so string concat
DEBUG_CONFIG_FILE_FULL_NAME = DEBUG_CONFIG_FILE_DIRECTORY + DEBUG_CONFIG_FILE_NAME



#Str name of the config in the strings file?
DEFAULT_CONFIG = {"device_id": "", "device_name": "NewPyonAir", "password": "newpyonair", "region": "Europe",
                         "device_eui": "", "application_eui": "", "app_key": "", "SSID": "", "fmt_version": "",
                         "wifi_password": "", "TEMP": "SHT35", "PM1": "OFF", "code_version": "",
                         "PM2": "SPS030", "GPS": "OFF", "PM1_id": "002", "PM2_id": "003", "TEMP_id": "001",
                         "GPS_id": "004", "interval": 15, "TEMP_period": 30, "GPS_period": 12, "PM1_init": 30,
                         "PM2_init": 30, "logging_lvl": "DEBUG", "lora_timeout": 20, "GPS_timeout": 20,
                         "config_timeout": 10, "fair_access": 30, "air_time": 75, "message_count": 0,
                         "transmission_date": 0, "LORA": "ON", "update": False, "port": 8000,
                         "server": "10.15.40.51",
                         "averagesPerHour" : 60}


#============================Config=================
