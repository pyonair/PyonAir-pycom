import strings as s
#from ubinascii import hexlify
#from machine import unique_id
#from network import LoRa
import os
import ujson
from Constants import *

#TODO: memory hog, sort this class - static?

class ConfigurationException(Exception):
    """
    Exception to be thrown if Exception occurs in configuration
    """
    #TODO: why?
    pass


class Configuration:

    def __init__(self,logger):
        self.logger= logger
        self.configuration = {} 
        #RM 
        
        self.read_configuration()
        print("CONFIG READ########################################")

    # Configuration Accessor/Getter
    def get_config(self, keys=None):
        """
        If keys are given, return corresponding values in a list, if one key is given, return the corresponding value,
        if no arguments are given, return the config dictionary
        :param keys: keys in configuration dictionary
        :type keys: None, list of keys or a single key
        :return: values in configuration dictionary
        :rtype: dict, list of any, any
        """
        #TODO: Warn if key not in dict
        if keys is None:
            return self.configuration
        if isinstance(keys, list):
            return list(self.configuration[k] for k in keys if k in self.configuration)
            #TODO remove this multi option
        else:
            return self.configuration[keys]

    # Configuration Mutator/Setter
    def set_config(self, new_config):
        """
        # Update configuration dict in code the running code
        :param new_config: set of new configuration key-value pairs
        :type new_config: dict
        """
        
        self.configuration.update(new_config)

    #  Saves keys and preferences to sd card
    def save_config(self, new_config):
        """
        Updates configuration dict in the running code and in the SD card as well
        :param new_config: set of new configuration key-value pairs
        :type new_config: dict
        """
        self.set_config(new_config)

        with open(s.root_path + CONFIG_FILE_NAME, 'w') as f:  # save credentials to sd card
            f.write(ujson.dumps(self.configuration))

    #  Reads and returns keys and preferences from sd card
    def read_configuration(self):
        """
        Read config file on SD card and load it to the configuration dict
        """
        #set to default
        self.configuration = DEFAULT_CONFIG
        

        #if no config file
        if CONFIG_FILE_NAME not in os.listdir(CONFIG_FILE_DIRECTORY):
            with open(CONFIG_FILE_FULL_NAME, 'w') as f:  # create new config file
                f.write(ujson.dumps(self.configuration))
                #self.set_config(str(self.configuration))

        #load config
        if CONFIG_FILE_NAME in os.listdir(CONFIG_FILE_DIRECTORY):
            with open(CONFIG_FILE_FULL_NAME, 'r') as f:
                self.set_config(ujson.loads(f.read()))
                self.logger.debug(str(self.configuration))


        #check for debug force overwrite.

        
        #Override Preferences - DEVELOPER USE ONLY - keep all overwrites here
        if DEBUG_CONFIG_FILE_NAME in os.listdir(DEBUG_CONFIG_FILE_DIRECTORY):
            self.logger.warning("Overriding configuration with the content of debug_config.json")
            
            with open(DEBUG_CONFIG_FILE_FULL_NAME, 'r') as f:
                self.set_config(ujson.loads(f.read()))
                self.logger.warning("Configuration changed to: " + str(self.configuration))


    # Returns True if the configuration file is complete
    def is_complete(self, logger):
        """
        Checks for missing keys and values in the configuration dict
        :param logger: status logger
        :type logger: LoggerFactory object
        :return: True if config is complete, False if not
        :rtype: bool
        """

        # Check if there are missing values
        if "" in self.get_config().values():
            logger.warning("There are missing values in the configuration")
            return False
        # Check if there are missing keys
        for key in self.default_configuration.keys():
            if key not in self.get_config().keys():
                print(key)
                logger.warning("There are missing keys in the configuration")
                return False
        else:
            return True

    #  Resets all configuration, then sets new device_id and device_EUI
    def reset_configuration(self, logger):
        """
        Resets configuration to the default one and fetches device_id and device_eui
        :param logger: status logger
        :type logger: LoggerFactory object
        """
        try:
            self.logger.warning("This wont work ") #TODO: this method needs sorting
            self.configuration.clear()  # clear configuration
            self.set_config(DEFAULT_CONFIG)  # set configuration to default

            #disable Lora configs -- use pybytes
            #self.set_config({"device_id": hexlify(unique_id()).upper().decode("utf-8")})  # set new device_id

            #lora = LoRa(mode=LoRa.LORAWAN)
            #self.set_config({"device_eui": hexlify(lora.mac()).upper().decode('utf-8')})  # set new device_EUI
            #del lora

            logger.info('Configurations were reset')
            logger.warning('Please configure your device!')
        except Exception as e:
            logger.exception('Failed to reset configurations')
            raise ConfigurationException(str(e))

    def getConfigDictionary(self):
        # TODO: that is a mess
        # global configuration dictionary
        #config = Configuration()
        return self.configuration
