

##Move all constants here. 

#Just filename not location/path
LOG_FILENAME="PyonAir.log"
#The name of the logger instance -- no need to change
DEFAULT_LOG_NAME="Pyonair"
LOG_LEVEL_KEY= "logging_lvl" #TODO : rename to something sensible



#config_filename = 'Settings.cfg'
CONFIG_FILE_NAME = "Settings.json"
CONFIG_FILE_DIRECTORY = "/sd"

#CONFIG_FILE_FULL_NAME = 
DEBUG_CONFIG_FILE_NAME = "debug_config.json"
DEBUG_CONFIG_FILE_DIRECTORY = "/flash"



#Str name of the config in the strings file?
DEFAULT_CONFIG = {"device_id": "", "device_name": "NewPyonAir", "password": "newpyonair", "region": "Europe",
                         "device_eui": "", "application_eui": "", "app_key": "", "SSID": "", "fmt_version": "",
                         "wifi_password": "", "TEMP": "SHT35", "PM1": "OFF", "code_version": "",
                         "PM2": "SPS030", "GPS": "OFF", "PM1_id": "002", "PM2_id": "003", "TEMP_id": "001",
                         "GPS_id": "004", "interval": 15, "TEMP_period": 30, "GPS_period": 12, "PM1_init": 30,
                         "PM2_init": 30, "logging_lvl": "DEBUG", "lora_timeout": 20, "GPS_timeout": 20,
                         "config_timeout": 10, "fair_access": 30, "air_time": 75, "message_count": 0,
                         "transmission_date": 0, "LORA": "ON", "update": False, "port": 8000,
                         "server": "10.15.40.51"}


#============================Config=================
