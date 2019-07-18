from network import LoRa
import socket
import struct
import time
import ubinascii
import os
from strings import headers_dict_v3
from configuration import config

header = headers_dict_v3['PMS5003']


def lora_thread(thread_name, log_file_name, logger, timeout):

    logger.info("Thread: {} started".format(thread_name))
    try:
        elapsed = 0

        # Initialise LoRa in LORAWAN mode.
        # Please pick the region that matches where you are using the device:
        # Asia = LoRa.AS923
        # Australia = LoRa.AU915
        # Europe = LoRa.EU868
        # United States = LoRa.US915
        lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, adr=True)

        # create an OTAA authentication parameters
        app_eui = ubinascii.unhexlify(config["app_eui"])
        app_key = ubinascii.unhexlify(config["app_key"])

        # join a network using OTAA (Over the Air Activation)
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

        # wait until the module has joined the network
        while not lora.has_joined():
            time.sleep(0.2)
            elapsed += 0.2
            if elapsed >= timeout:
                return

        # create a LoRa socket
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # set the LoRaWAN data rate
        s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        s.setblocking(True)

        logger.info("joined LoRa network")
        logger.info('bandwidth:' + str(lora.bandwidth()))
        logger.info('spreading factor:' + str(lora.sf()))

        if log_file_name not in os.listdir('/sd'):
            logger.error('{} does not exist, failed to read data to be sent over LoRaWAN'.format(log_file_name))
        else:
            try:
                with open('/sd/' + log_file_name, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        stripped_line = line[:-1]
                        split_line_lst = stripped_line.split(',')
                        named_line = dict(zip(header, split_line_lst))
                        timestamp = int(named_line['timestamp'])
                        pm10 = int(named_line['PM10'])
                        pm25 = int(named_line['PM25'])
                        payload = struct.pack('HBB', timestamp, pm10, pm25)
                        s.send(payload)
                        logger.info("Thread: {} sent payload".format(thread_name))
            except Exception as e:
                logger.error(e)
                logger.error("Failed to send data over LoRaWAN")
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Thread: {} finished".format(thread_name))