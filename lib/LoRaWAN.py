from Configuration import config
import strings as s
from helper import blink_led, lora_lock, minutes_of_the_month
from RingBuffer import RingBuffer
import struct
import os
from network import LoRa
import socket
import ubinascii
import time
# import machine
# import ujson


class LoRaWAN:
    def __init__(self, logger):

        self.logger = logger
        self.message_limit = int(float(config.get_config("fair_access")) / (float(config.get_config("air_time")) / 1000))
        self.transmission_date = config.get_config("transmission_date")  # last date when lora was transmitting
        today = time.gmtime()
        date = str(today[0]) + str(today[1]) + str(today[2])
        if self.transmission_date == date:  # if device was last transmitting today
            self.message_count = config.get_config("message_count")  # get number of messages sent today
        else:
            self.message_count = 0  # if device was last transmitting a day or more ago, reset message_count for the day
            self.transmission_date = date
            config.save_configuration({"message_count": self.message_count, "transmission_date": date})

        regions = {"Europe": LoRa.EU868, "Asia": LoRa.AS923, "Australia": LoRa.AU915, "United States": LoRa.US915}
        region = regions[config.get_config("region")]

        self.lora = LoRa(mode=LoRa.LORAWAN, region=region, adr=True)

        # create an OTAA authentication parameters
        app_eui = ubinascii.unhexlify(config.get_config("application_eui"))
        app_key = ubinascii.unhexlify(config.get_config("app_key"))

        # join a network using OTAA (Over the Air Activation)
        self.lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

        # create a LoRa socket
        self.lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # request acknowledgment of data sent
        # self.lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

        # do not request acknowledgment of data sent
        self.lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)

        # sets timeout for sending data
        self.lora_socket.settimeout(int(config.get_config("lora_timeout")) * 1000)

        # set up callback for receiving downlink messages
        # self.lora.callback(trigger=LoRa.RX_PACKET_EVENT, handler=self.lora_recv)

        # initializes circular lora stack to back up data up to about 22.5 days depending on the length of the month
        self.lora_buffer = RingBuffer(self.logger, s.processing_path, s.lora_file_name, 31 * self.message_limit, 100)

        try:  # this fails if the buffer is empty
            self.check_date()  # remove messages that are over a month old
        except Exception as e:
            pass

    # def lora_recv(self, arg):
    #
    #     message = self.lora_socket.recv(600)
    #     self.logger.info("Lora message received: {}".format(message))
    #
    #     if message == bytes([1]):
    #         self.logger.info("Reset triggered over LoRa")
    #         self.logger.info("rebooting...")
    #         machine.reset()
    #
    #     message = message.decode()
    #     try:
    #         new_config = ujson.loads(message)
    #     except Exception as e:
    #         self.logger.info("Unknown command")
    #         return
    #
    #     for key in new_config.keys():
    #         if key not in config.default_configuration.keys():
    #             self.logger.info("Unknown command")
    #             return
    #
    #     self.logger.info("New configuration key-value pairs received over LoRa")
    #     self.logger.info(new_config)
    #     config.save_configuration(new_config)
    #     self.logger.info("rebooting...")
    #     machine.reset()

    def lora_send(self, arg1, arg2):

        if lora_lock.locked():
            self.logger.debug("Waiting for other lora thread to finish")
        with lora_lock:
            self.logger.debug("LoRa thread started")

            try:
                self.check_date()  # remove messages that are over a month old

                if self.lora.has_joined():
                    self.logger.debug("LoRa connected")
                else:
                    raise Exception("LoRa is not connected")

                if s.lora_file_name not in os.listdir(s.root_path + s.processing):
                    raise Exception('LoRa - File: {} does not exist'.format(s.lora_file_name))
                else:
                    port, payload = self.get_sending_details()

                    self.lora_socket.bind(port)  # bind to port to decode at backend
                    self.lora_socket.send(payload)  # send payload to the connected socket
                    self.logger.debug("LoRa - sent payload")

                    self.message_count += 1  # increment number of files sent over LoRa today
                    config.save_configuration({"message_count": self.message_count})  # save number of messages today

                    # remove message sent
                    self.lora_buffer.remove_head()

            except Exception as e:
                self.logger.exception("Sending payload over LoRaWAN failed")
                blink_led((0x550000, 0.4, True))

    def get_sending_details(self):

        buffer_line = self.lora_buffer.read()
        buffer_lst = buffer_line.split(',')  # convert string to a list of strings

        # get structure and port from format
        fmt = buffer_lst[2]  # format is third item in the list
        fmt_dict = {"TPP": s.TPP, "TP": s.TP, "PP": s.PP, "P": s.P, "T": s.T, "G": s.G}
        port_struct_dict = fmt_dict[fmt]  # get dictionary corresponding to the format
        port = port_struct_dict["port"]  # get port corresponding to the format
        structure = port_struct_dict["structure"]  # get structure corresponding to the format

        # cast message according to format to form valid payload
        lst_message = buffer_lst[3:]  # chop year, month and format off
        cast_lst_message = []
        for i in range((len(structure) - 1)):  # iterate for length of structure having '<' stripped
            if structure[i + 1] == 'f':  # iterate through structure ignoring '<'
                cast_lst_message.append(float(lst_message[i]))  # cast to float if structure is 'f'
            else:
                cast_lst_message.append(int(lst_message[i]))  # cast to int otherwise

        # pack payload
        self.logger.debug("Sending over LoRa: " + str(cast_lst_message))
        payload = struct.pack(structure, *cast_lst_message)  # define payload with given structure and list of averages

        return port, payload

    # removes messages from end of lora stack until they are all within a month
    def check_date(self):
        buffer_line = self.lora_buffer.read(read_tail=True)  # read the tail of the lora_buffer
        buffer_lst = buffer_line.split(',')  # convert string to a list of strings
        time_now = time.gmtime()  # get current date

        # get year, month and minutes of the month now
        year_now, month_now, minutes_now = time_now[0], time_now[1], minutes_of_the_month()

        # get year, month and minutes of the month of the last message in the lora_buffer
        year_then, month_then, minutes_then = int(buffer_lst[0]) + 2000, int(buffer_lst[1]), int(buffer_lst[4])

        # logic to decide if message is older than a month
        if year_then < year_now or month_then < month_now:
            if (month_then + 1 == month_now) or (month_then == 12 and month_now == 1 and year_then + 1 == year_now):
                if minutes_then < minutes_now + 24*60:
                    self.lora_buffer.remove_tail()  # remove message
                    self.check_date()  # call recursively
            else:
                self.lora_buffer.remove_tail()  # remove message
                self.check_date()  # call recursively
