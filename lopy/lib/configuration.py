import network
from network import WLAN
import usocket as socket
from html import html_form, html_acknowledgement
import machine
import time
import pycom
import gc
from strings import config_filename
import os
import _thread

config_lock = _thread.allocate_lock()


def config_thread(id, logger, timeout):
    """
    Thread that turns on access point on the device to modify configurations. Name of access point: PmSensor
    Password: pmsensor Enter 192.168.4.10 on device browser to get configuration form. Indicator LEDs:
    Blue - Access point turned on, not connected, Green - Connected, configuration is open on browser,
    Red - An error has occured
    The device automatically reboots and applies modifications upon successful configuration.
    :param id: Thread id
    :type id: str
    :param logger: status logger
    :type logger: LoggerFactory object
    :param timeout: timeout (in seconds) for user configuration
    :type timeout: int
    """

    #  Only one of this thread is allowed to run at a time
    if not config_lock.locked():
        with config_lock:

            logger.info("Thread: {} started".format(id))

            # set pycom up as access point
            wlan = network.WLAN(mode=WLAN.AP, ssid='PmSensor')
            # Connect to PmSensor using password pmsensor
            wlan.init(mode=WLAN.AP, ssid='PmSensor', auth=(WLAN.WPA2, 'pmsensor'), channel=1, antenna=WLAN.INT_ANT)
            # Load HTML via entering 192,168.4.10 to your browser
            wlan.ifconfig(id=1, config=('192.168.4.10', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

            logger.info('Access point turned on as PmSensor')
            logger.info('Configuration website can be accessed at 192.168.4.10')

            address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Accept stations from all addresses
            sct = socket.socket()  # Create socket for communication
            sct.settimeout(timeout)  # session times out after x seconds
            gc.collect()  # frees up unused memory if there was a previous connection
            sct.bind(address)  # Bind address to socket
            sct.listen(1)  # Allow one station to connect to socket

            pycom.heartbeat(False)
            pycom.rgbled(0x0000FF)  # Blue LED - Initialized, waiting for connection

            reboot = False

            if get_configuration(sct, logger):
                reboot = True

            wlan.deinit()  # turn off wifi
            pycom.heartbeat(True)  # disable indicator LEDs
            gc.collect()

            if reboot:
                logger.info('rebooting...')
                machine.reset()


#  Sends html form over wifi and receives data from the user
def get_configuration(sct, logger):
    try:
        while True:
            client, address = sct.accept()  # wait for new connection
            client.send(html_form)  # send html page with form to submit by the user
            pycom.rgbled(0x00FF00)  # Green LED - Connection successful
            received_data = str(client.recv(3000))  # wait for client response
            #  print("received data:", received_data)
            if process_data(client, received_data, logger):
                return True
    except:
        pycom.rgbled(0xFF0000)  # Red LED - Connection timeout
        logger.warning('Wifi configuration session timed out')
        time.sleep(3)
        return False


#  Parses keys and preferences from data received
def process_data(client, received_data, logger):

    index = [None] * 4
    config_names = {0: 'APP_KEY', 1: 'APP_EUI', 2: 'interval'}

    for i in range(0, 3):  # find indices in received message
        index[i] = received_data.rfind(config_names[i])

    if -1 not in index[0:3]:  # if all keys were found in the message, cut them up to strings
        APP_KEY = received_data[(index[0] + 8):index[1] - 1]
        logger.info('APP_KEY: {}'.format(APP_KEY))
        APP_EUI = received_data[(index[1] + 8):index[2] - 1]
        logger.info('APP_EUI: {}'.format(APP_EUI))
        index[3] = received_data.find("\r", index[2])
        if index[3] != -1:  # last key is not in the end of the message
            interval = received_data[(index[2] + 9):index[3]]
            logger.info("interval: {} minutes".format(interval))
        else:  # last key is in the end of the message
            interval = received_data[(index[2] + 9):-1]
            logger.info("interval: {} minutes".format(interval))

        client.send(html_acknowledgement.format(APP_KEY, APP_EUI, interval))  # sends acknowledgement to user
        client.close()
        logger.info('Configuration data received from user')

        config_values = {'APP_KEY': APP_KEY, 'APP_EUI': APP_EUI, 'interval': interval}

        if save_configuration(logger, config_values):
            return True
        else:
            logger.error('Could not save config file')
            raise Exception('Could not save config file')

    return False


#  Saves keys and preferences to sd card
def save_configuration(logger, config_values):
    try:
        with open('/sd/config.txt', 'w') as f:  # save credentials to sd card
            f.write(config_values['APP_KEY'] + '\r\n' + config_values['APP_EUI'] + '\r\n' +
                    config_values['interval'] + '\r\n')
        logger.info('Configuration saved to SD card')
        return True
    except:
        return False


#  Reads and returns keys and preferences from sd card
def read_configuration(logger):

    config_values = {'APP_KEY': None, 'APP_EUI': None, 'interval': None}

    if config_filename not in os.listdir('/sd'):
        logger.warning('{} does not exist, failed to configure device'.format(config_filename))
        return
    with open('/sd/' + config_filename, 'r') as f:
        lines = f.readlines()
        config_values['APP_KEY'] = lines[0][0:-2]
        config_values['APP_EUI'] = lines[1][0:-2]
        config_values['interval'] = float(lines[2][0:-2]) * 60  # seconds
        logger.info('APP_KEY: {}'.format(config_values['APP_KEY']))
        logger.info('APP_EUI: {}'.format(config_values['APP_EUI']))
        logger.info('interval: {} seconds'.format(config_values['interval']))
        return config_values
