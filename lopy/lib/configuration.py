from strings import config_filename
from ubinascii import hexlify
from machine import unique_id
from network import LoRa
import os
import ujson

config = {}

default_config = {"device_id": "", "device_name": "NewPmSensor", "password": "pmsensor", "region": "LoRa.EU868",
                  "device_eui": "", "application_eui": "", "app_key": "", "application_id": "",
                  "access_key": "", "raw_interval": 12, "PM1": True, "PM2": True, "TEMP": True,
                  "GPS": True, "PM1_id": "001", "PM2_id": "002", "TEMP_id": "001", "GPS_id": "001",
                  "PM_interval": 15, "TEMP_interval": 15, "GPS_interval": 12,
                  "logging_lvl": "Warning"}


#  Saves keys and preferences to sd card
def save_configuration(logger, config_json_str):

    config.update(PM1=False, PM2=False, TEMP=False, GPS=False)

    config.update(ujson.loads(config_json_str))

    try:
        with open('/sd/' + config_filename, 'w') as f:  # save credentials to sd card
            f.write(ujson.dumps(config))
        logger.info('Configuration saved to SD card')
        return True
    except:
        return False


#  Reads and returns keys and preferences from sd card
def read_configuration(logger):

    if config_filename not in os.listdir('/sd'):
        logger.warning('{} does not exist, creating new config file'.format(config_filename))
        with open('/sd/' + config_filename, 'w') as f:  # create new config file
            f.write(ujson.dumps(default_config))
            config.update(default_config)
    else:
        with open('/sd/' + config_filename, 'r') as f:
            config.update(ujson.loads(f.read()))


#  Resets all configuration, then sets new device_id and device_EUI
def reset_configuration(logger):

    try:
        config.clear()  # clear configuration
        config.update(default_config)  # set configuration to default

        config.update(device_id=hexlify(unique_id()).upper().decode("utf-8"))  # set new device_id

        lora = LoRa(mode=LoRa.LORAWAN)
        config.update(device_eui=hexlify(lora.mac()).upper().decode('utf-8'))  # set new device_EUI
        del lora

        print(config)
        logger.info('Configurations were reset')
    except:
        logger.error('Failed to reset configurations')
