from Configuration import config
import strings as s
from helper import blink_led
import struct
import os
import _thread

# Having a lock is necessary, because it is possible to have two lora threads running at the same time
lora_lock = _thread.allocate_lock()


def lora_thread(thread_name, logger, data_type, lora, lora_socket):
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

    if lora_lock.locked():
        logger.debug("Waiting for other lora thread to finish")
    with lora_lock:
        logger.debug("Thread: {} started".format(thread_name))

        try:
            if lora.has_joined():
                logger.debug("LoRa connected")
            else:
                raise Exception("LoRa is not connected")

            if data_type == "PM":
                lora_socket.bind(1)
                log_file_name = s.PM_lora_file

                """Set the structure of the bytes to send over lora according to which sensors are defined. long_struct is 
                used for temp+2PM, while short_struct is used for temp+1PM. Synchronized with back-end according to version 
                number"""
                structure = s.lora_long_struct
                if config.get_config(s.PM1) == "OFF" or config.get_config(s.PM2) == "OFF":
                    structure = s.lora_short_struct

            elif data_type == "GPS":
                lora_socket.bind(2)
                log_file_name = s.GPS_lora_file
                structure = s.lora_gps_struct

            if log_file_name not in os.listdir(s.lora_path[:-1]):  # Strip '/' from the end of path
                raise Exception('Thread: {} - {} does not exist'.format(thread_name, log_file_name))
            else:
                with open(s.lora_path + log_file_name, 'r') as f:

                    # read all lines from lora.csv.tosend
                    line = f.readline()
                    stripped_line = line[:-1]  # strip /n
                    split_line_lst = stripped_line.split(',')  # split line to a list of strings

                    # cast string values to appropriate data type
                    casted_line_list = []
                    for i in range((len(structure)-1)):  # iterate for length of structure having '<' stripped
                        if structure[i+1] == 'f':  # iterate through structure ignoring '<'
                            casted_line_list.append(float(split_line_lst[i]))  # cast to float if structure is 'f'
                        else:
                            casted_line_list.append(int(split_line_lst[i]))  # cast to int otherwise

                    # pack payload and send it over LoRa
                    logger.debug("Sending over lora: " + str(casted_line_list))
                    payload = struct.pack(structure, *casted_line_list)  # define payload with given structure and list of averages
                    lora_socket.send(payload)  # send payload to the connected socket
                    logger.debug("Thread: {} sent payload".format(thread_name))

                    # remove file sent
                    logger.debug("Thread: {} removing file: {}".format(thread_name, log_file_name))
                    os.remove(s.lora_path + log_file_name)

        except Exception as e:
            logger.exception("Sending payload over LoRaWAN failed")
            blink_led(colour=0x770000, delay=0.5, count=1)
        finally:
            logger.debug("Thread: {} finished".format(thread_name))
