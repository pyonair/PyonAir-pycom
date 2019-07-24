from network import LoRa
import socket
import struct
import time
import ubinascii
import os
from strings import headers_dict_v4
from configuration import config
import _thread


#  Only one thread can use lora at a time
lora_lock = _thread.allocate_lock()

header = headers_dict_v4['PMS5003']


def lora_thread(thread_name, sensor_name, log_file_name, logger, timeout):

    logger.info(" Sensor {} spawned {} thread".format(sensor_name, thread_name))

    if lora_lock.locked():
        logger.info(" Sensor {} - Thread: {} - Waiting for other LoRa Thread to finish".format(sensor_name, thread_name))
    with lora_lock:
        logger.info(" Sensor {} - Thread: {} - Attempting to join LoRa Network".format(sensor_name, thread_name))
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

            logger.info("Sensor {} - Thread: {} - joined LoRa network".format(sensor_name, thread_name))
            logger.info('bandwidth:' + str(lora.bandwidth()))
            logger.info('spreading factor:' + str(lora.sf()))

            if log_file_name not in os.listdir('/sd'):
                logger.error('Sensor {} - Thread: {} - {} does not exist, failed to read data to be sent over LoRaWAN'.format(sensor_name, thread_name, log_file_name))
            else:
                try:
                    with open('/sd/' + log_file_name, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            stripped_line = line[:-1]
                            split_line_lst = stripped_line.split(',')
                            named_line = dict(zip(header, split_line_lst))
                            timestamp = int(named_line['timestamp'])
                            sensor_id = int(named_line['sensor_id'])
                            pm10 = int(named_line['PM10'])
                            pm25 = int(named_line['PM25'])
                            payload = struct.pack('HHBB', timestamp, sensor_id, pm10, pm25)
                            s.send(payload)
                            logger.info("Sensor {} - Thread: {} sent payload".format(sensor_name, thread_name))
                except Exception as e:
                    logger.error(e)
                    logger.error("Sensor {} - Thread: {} failed to send data over LoRaWAN".format(sensor_name, thread_name))
        except Exception as e:
            logger.error(e)
        finally:
            logger.info("Sensor {} - Thread: {} finished".format(sensor_name, thread_name))
