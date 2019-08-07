from strings import config_filename
from ubinascii import hexlify
from machine import unique_id
from network import LoRa
import os
import ujson


class ConfigurationException(Exception):
    """
    Exception to be thrown if Exception occurs in configuration
    """
    pass


class Configuration:

    def __init__(self):

        self.configuration = {}

        self.default_configuration = {"device_id": "", "device_name": "NewPyonAir", "password": "newpyonair",
                                      "region": "Europe", "device_eui": "", "application_eui": "",
                                      "app_key": "", "SSID": "", "wifi_password": "", "raw_freq": 15,
                                      "PM1": "PMS5003", "PM2": "SPS030", "GPS": "OFF", "PM1_id": "002",
                                      "PM2_id": "003", "TEMP_id": "001", "GPS_id": "004", "PM_interval": 15,
                                      "TEMP_freq": 5, "GPS_freq": 12, "logging_lvl": "Warning", "lora_timeout": 60}

    # Configuration Accessor/Getter
    def get_config(self, keys=None):
        if keys is None:
            return self.configuration
        if isinstance(keys, list):
            return list(self.configuration[k] for k in keys if k in self.configuration)
        else:
            return self.configuration[keys]

    # Configuration Mutator/Setter
    def set_config(self, new_config):
        self.configuration.update(new_config)

    # Returns if all keys are set in the configuration
    def is_complete(self):
        if "" in self.configuration.values():
            return False
        else:
            return True

    #  Saves keys and preferences to sd card
    def save_configuration(self, logger, config_json_str):

        self.set_config(ujson.loads(config_json_str))

        with open('/sd/' + config_filename, 'w') as f:  # save credentials to sd card
            f.write(ujson.dumps(self.configuration))
        logger.info('Configuration saved to SD card')

    #  Reads and returns keys and preferences from sd card
    def read_configuration(self, logger):

        if config_filename not in os.listdir('/sd'):
            logger.warning('{} does not exist, creating new config file'.format(config_filename))
            with open('/sd/' + config_filename, 'w') as f:  # create new config file
                f.write(ujson.dumps(self.default_configuration))
                self.set_config(self.default_configuration)
        else:
            with open('/sd/' + config_filename, 'r') as f:
                self.set_config(ujson.loads(f.read()))

    #  Resets all configuration, then sets new device_id and device_EUI
    def reset_configuration(self, logger):

        try:
            self.configuration.clear()  # clear configuration
            self.set_config(self.default_configuration)  # set configuration to default

            self.set_config({"device_id": hexlify(unique_id()).upper().decode("utf-8")})  # set new device_id

            lora = LoRa(mode=LoRa.LORAWAN)
            self.set_config({"device_eui": hexlify(lora.mac()).upper().decode('utf-8')})  # set new device_EUI
            del lora

            logger.info('Configurations were reset')
        except Exception as e:
            logger.exception('Failed to reset configurations')
            raise ConfigurationException(str(e))


config = Configuration()
