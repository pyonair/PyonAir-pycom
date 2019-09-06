import strings as s
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
        self.default_configuration = s.default_configuration

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

    # Returns True if the configuration file is complete
    def is_complete(self, logger):
        # Check if there are missing values
        if "" in self.configuration.values():
            logger.warning("There are missing values in the configuration")
            return False
        # Check if there are missing keys
        for key in self.default_configuration.keys():
            if key not in self.get_config().keys():
                logger.warning("There are missing keys in the configuration")
                return False
        else:
            return True

    #  Saves keys and preferences to sd card
    def save_configuration(self, new_config):

        self.set_config(new_config)

        with open(s.root_path + s.config_filename, 'w') as f:  # save credentials to sd card
            f.write(ujson.dumps(self.configuration))

    #  Reads and returns keys and preferences from sd card
    def read_configuration(self):

        if s.config_filename not in os.listdir('/sd'):
            with open('/sd/' + s.config_filename, 'w') as f:  # create new config file
                f.write(ujson.dumps(self.default_configuration))
                self.set_config(self.default_configuration)
        else:
            with open('/sd/' + s.config_filename, 'r') as f:
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
            logger.warning('Please configure your device!')
        except Exception as e:
            logger.exception('Failed to reset configurations')
            raise ConfigurationException(str(e))


config = Configuration()
