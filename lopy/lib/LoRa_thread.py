from network import LoRa
import socket
import struct
import ubinascii
import os
from configuration import config
from helper import blink_led
import _thread
import strings as s

# Having a lock is necessary, because it is possible to have two lora threads running at the same time
lora_lock = _thread.allocate_lock()


def lora_thread(thread_name, logger, is_def, timeout):
    """
    Function that connects to the LoRaWAN network using OTAA and sends sensor averages from the tosend file.
     It is run as a thread by the send_over_lora method defined in tasks.py
    :param thread_name: Name of the thread for identification purposes
    :type thread_name: str
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    :param timeout: Timeout for LoRa to send over data seconds
    :type timeout: int
    """

    # Only send averages if PM1 or PM2 or both sensors are enabled and have gathered data
    if is_def["PM1"] or is_def["PM2"]:

        if lora_lock.locked():
            logger.info("Waiting for other lora thread to finish")
        with lora_lock:
            logger.info("Thread: {} started".format(thread_name))

            try:
                # default region is Europe
                region = LoRa.EU868

                # set region according to configuration - using either region name, or region code
                if config["region"] == "AS923" or config["region"] == "Asia":
                    region = LoRa.AS923
                elif config["region"] == "AU915" or config["region"] == "Australia":
                    region = LoRa.AU915
                elif config["region"] == "US915" or config["region"] == "United States":
                    region = LoRa.US915

                lora = LoRa(mode=LoRa.LORAWAN, region=region, adr=True)

                # create an OTAA authentication parameters
                app_eui = ubinascii.unhexlify(config["application_eui"])
                app_key = ubinascii.unhexlify(config["app_key"])

                # join a network using OTAA (Over the Air Activation)
                lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=timeout*1000)

                # wait until the module has joined the network
                while not lora.has_joined():
                    pass

                # create a LoRa socket
                soc = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

                # set the LoRaWAN data rate
                soc.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

                # make the socket blocking
                # (waits for the data to be sent and for the 2 receive windows to expire)
                soc.setblocking(True)

                logger.info("Thread: {} - joined LoRa network".format(thread_name))
                logger.info('bandwidth:' + str(lora.bandwidth()))
                logger.info('spreading factor:' + str(lora.sf()))

                log_file_name = s.lora_file

                # Set the structure of the bytes to send over lora according to which sensors are defined
                structure = 'HHhhHHBBHHBBH'
                if not (is_def["PM1"] and is_def["PM2"]):
                    structure = 'HHhhHHBBH'

                if log_file_name not in os.listdir(s.lora_path[:-1]):  # Strip '/' from the end of path
                    raise Exception('Thread: {} - {} does not exist'.format(thread_name, log_file_name))
                else:
                    with open(s.lora_path + log_file_name, 'r') as f:

                        # read all lines from lora.csv.tosend
                        lines = f.readlines()
                        for line in lines:
                            stripped_line = line[:-1]  # strip /n
                            split_line_lst = stripped_line.split(',')  # split line to a list of values
                            int_line = list(map(int, split_line_lst))  # cast str list to int list
                            payload = struct.pack(structure, *int_line)  # define payload with given structure and list of averages

                        soc.send(payload)  # send payload to the connected socket
                        logger.info("Thread: {} sent payload".format(thread_name))

            except Exception as e:
                logger.exception("Sending averages over LoRaWAN failed")
                blink_led(colour=0x770000, delay=0.5, count=1)
            finally:
                logger.info("Thread: {} finished".format(thread_name))
