import network
from network import WLAN
import usocket as socket
from html import html_form, html_acknowledgement
import time
import pycom
import gc
from strings import config_filename
import os


def request_credentials(sd, sct):

    index = [None] * 4
    credentials = {0: 'APP_KEY', 1: 'APP_EUI', 2: 'interval'}

    try:
        while True:
            # print('Waiting for new connection')
            client, address = sct.accept()
            # print('Client connected at: ', address)
            client.send(html_form)  # send html page with form to submit by the user
            pycom.rgbled(0x00FF00)  # Green LED - Connection successful
            received_data = str(client.recv(3000))  # wait for client response
            for i in range(0, 3):  # find indices in received message
                index[i] = received_data.rfind(credentials[i])
            if -1 not in index[0:3]:  # if all keys were found in the message, cut them up to strings
                APP_KEY = received_data[(index[0] + 8):index[1] - 1]
                print("APP_KEY:", APP_KEY)
                APP_EUI = received_data[(index[1] + 8):index[2] - 1]
                print("APP_EUI:", APP_EUI)
                index[3] = received_data.find("\r", index[2])
                if index[3] != -1:  # last key is not in the end of the message
                    interval = received_data[(index[2] + 9):index[3]]
                    print("interval: {} minutes".format(interval))
                else:  # last key is in the end of the message
                    interval = received_data[(index[2] + 9):-1]
                    print("interval: {} minutes".format(interval))
                client.send(html_acknowledgement.format(APP_KEY, APP_EUI, interval))  # sends acknowledgement to user
                client.close()
                sd.log_status(sd.INFO, 'Config data received')
                try:
                    with open('/sd/config.txt', 'w') as f:  # save credentials to sd card
                        f.write(APP_KEY + '\r\n' + APP_EUI + '\r\n' + interval + '\r\n')
                    sd.log_status(sd.INFO, 'Configuration saved to SD card')
                    sd.get_config()  # Load new configuration from sd card
                except:
                    sd.log_status(sd.ERROR, 'Could not save config file')
                finally:
                    return
    except:
        pycom.rgbled(0xFF0000)  # Red LED - Connection timeout
        sd.log_status(sd.WARN, 'Wifi configuration session timed out')
        time.sleep(3)
        return


def config_thread(sd, id):

    print("Thread: {} started".format(id))

    # set pycom up as access point
    wlan = network.WLAN(mode=WLAN.AP, ssid='MVP')
    # Connect to MVP using the passowrd pmsensor
    wlan.init(mode=WLAN.AP, ssid='MVP', auth=(WLAN.WPA2, 'pmsensor'), channel=1, antenna=WLAN.INT_ANT)
    # Load HTML via entering 192,168.4.10 to your browser
    wlan.ifconfig(id=1, config=('192.168.4.10', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

    print('Access point turned on as MVP')
    print('Configuration website can be accessed at 192.168.4.10')

    address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Accept stations from all addresses
    sct = socket.socket()  # Create socket for communication
    sct.settimeout(300)  # session times out after x seconds
    gc.collect()  # frees up unused memory if there was a previous connection
    sct.bind(address)  # Bind address to socket
    sct.listen(1)  # Allow one station to connect to socket

    pycom.heartbeat(False)
    pycom.rgbled(0x0000FF)  # Blue LED - Initialized, waiting for connection

    request_credentials(sd, sct)

    wlan.deinit()  # turn off wifi
    pycom.heartbeat(True)  # disable indicator LEDs
    gc.collect()


def get_config(logger):
    if config_filename not in os.listdir('/sd'):
        logger.warning('{} does not exist, failed to configure device'.format(config_filename))
        return
    with open('/sd/' + config_filename, 'r') as f:
        lines = f.readlines()
        APP_KEY = lines[0][0:-2]
        APP_EUI = lines[1][0:-2]
        interval = lines[2][0:-2]
        print("APP_KEY:", APP_KEY)
        print("APP_EUI:", APP_EUI)
        print("interval:", interval)
