import network
from network import WLAN
import usocket as socket
from config_page import get_html_form
import machine
import pycom
import gc
from Configuration import config
from helper import wifi_lock, led_lock, blink_led
from RtcDS1307 import clock
import ujson


def new_config(logger, arg):
    """
    Thread that turns on access point on the device to modify configurations. Name of access point: PmSensor
    Password: pmsensor Enter 192.168.4.10 on device browser to get configuration form. Indicator LEDs:
    Blue - Access point turned on, not connected, Green - Connected, configuration is open on browser,
    Red - An error has occured
    The device automatically reboots and applies modifications upon successful configuration.
    :param thread_name: Thread id
    :type thread_name: str
    :param logger: status logger
    :type logger: LoggerFactory object
    :param timeout: timeout (in seconds) for user configuration
    :type timeout: int
    """

    #  Only one of this thread is allowed to run at a time
    if not wifi_lock.locked():
        with wifi_lock:

            logger.info("New configuration setup started")

            # Config uses LED colours to indicate the state of the connection - lock is necessary to disable error pings
            led_lock.acquire(1)

            # set pycom up as access point
            wlan = network.WLAN(mode=WLAN.AP, ssid=config.get_config("device_name"))
            # Connect to PmSensor using password set by the user
            wlan.init(mode=WLAN.AP, ssid=config.get_config("device_name"), auth=(WLAN.WPA2, config.get_config("password")), channel=1,
                      antenna=WLAN.INT_ANT)
            # Load HTML via entering 192,168.4.10 to browser
            wlan.ifconfig(id=1, config=('192.168.4.10', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

            logger.info('Access point turned on as {}'.format(config.get_config("device_name")))
            logger.info('Configuration website can be accessed at 192.168.4.10')

            address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Accept stations from all addresses
            sct = socket.socket()  # Create socket for communication
            sct.settimeout(config.get_config("config_timeout"))  # session times out after x seconds
            gc.collect()  # frees up unused memory if there was a previous connection
            sct.bind(address)  # Bind address to socket
            sct.listen(1)  # Allow one station to connect to socket

            pycom.rgbled(0x000055)  # Blue LED - waiting for connection

            get_new_config(sct, logger)

            wlan.deinit()  # turn off wifi
            gc.collect()

            logger.info('rebooting...')
            machine.reset()


#  Sends html form over wifi and receives data from the user
def get_new_config(sct, logger):
    try:
        while True:
            try:
                client, address = sct.accept()  # wait for new connection
            except Exception as e:
                raise Exception("Configuration timeout")
            client.send(get_html_form())  # send html page with form to submit by the user
            pycom.rgbled(0x005500)  # Green LED - Connection successful
            received_data = str(client.recv(3000))  # wait for client response
            # logger.debug(received_data)
            client.close()  # socket has to be closed because of the loop
            if process_data(received_data, logger):
                return
    except Exception as e:
        logger.exception("Failed to configure the device")
        led_lock.release()
        blink_led((0x550000, 3, True))  # Red LED - Error
        return


def process_data(received_data, logger):

    #  find json string in received message
    first_index = received_data.rfind('time_begin')
    last_index = received_data.rfind('time_end')

    if first_index != -1 and last_index != -1:
        config_time_str = received_data[(first_index + len('time_begin')):last_index]
        config_time_lst = config_time_str.split(':')
        config_time_lst[0] = config_time_lst[0][2:]
        h_yr, h_mnth, h_day, h_hr, h_min, h_sec = int(config_time_lst[0], 16), int(config_time_lst[1], 16), \
                                                  int(config_time_lst[2], 16), int(config_time_lst[3], 16), \
                                                  int(config_time_lst[4], 16), int(config_time_lst[5], 16)
        try:
            clock.set_time(h_yr, h_mnth, h_day, h_hr, h_min, h_sec)
            logger.info('RTC module calibrated via WiFi')
        except Exception:
            logger.warning('RTC module is not available for calibration via WiFi')

    #  find json string in received message
    first_index = received_data.rfind('json_str_begin')
    last_index = received_data.rfind('json_str_end')

    if first_index != -1 and last_index != -1:
        config_json_str = received_data[(first_index + len('json_str_begin')):last_index]
        new_config_dict = ujson.loads(config_json_str)

        if len(config_json_str) >= 1000:
            logger.error('Received configurations are too long')
            logger.info('Enter configurations with valid length')
            return False  # keep looping - wait for new message from client

        logger.info('Configuration data received from user')
        config.save_configuration(new_config_dict)
        return True

    return False  # keep looping - wait for new message from client
