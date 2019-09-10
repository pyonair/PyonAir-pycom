import machine
from machine import RTC, Timer
from averages import get_sensor_averages
from helper import seconds_to_first_event
from Configuration import config
import GpsSIM28
import _thread
import time


class EventScheduler:
    def __init__(self, logger, data_type, lora):

        #  Arguments
        self.logger = logger
        self.data_type = data_type
        self.lora = lora

        #  Attributes
        if self.data_type == "sensors":
            self.interval_s = int(float(config.get_config("interval"))*60)
            if self.interval_s < 15 * 60:
                self.logger.warning("Interval is less than 15 mins - real time transmission is not guaranteed")
        elif self.data_type == "gps":
            self.interval_s = int(float(config.get_config("GPS_freq"))*3600)
        self.s_to_next_lora = None
        self.first_alarm = None
        self.periodic_alarm = None
        self.random_alarm = None

        #  Start scheduling events
        self.start_events()

    #  Calculates time (s) until the first event, and sets up an alarm
    def start_events(self):
        first_event_s = seconds_to_first_event(self.interval_s)
        self.first_alarm = Timer.Alarm(self.first_event, s=first_event_s, periodic=False)

    def first_event(self, arg):
        #  set up periodic alarm with specified interval to calculate averages
        self.periodic_alarm = Timer.Alarm(self.periodic_event, s=self.interval_s, periodic=True)
        self.periodic_event(arg)

    def periodic_event(self, arg):
        if self.data_type == "gps":
            #  get position from gps to be sent over LoRA
            _thread.start_new_thread(GpsSIM28.get_position, (self.logger, self.lora))

        elif self.data_type == "sensors":
            #  flash averages of PM data to sd card to be sent over LoRa
            get_sensor_averages(logger=self.logger, lora=self.lora)

            if self.lora is not False:  # Schedule LoRa messages if LoRa is enabled
                # if device was last transmitting a day or more ago, reset message_count for the day
                today = time.gmtime()
                date = str(today[0]) + str(today[1]) + str(today[2])
                if self.lora.transmission_date != date:
                    self.lora.message_count = 0
                    self.lora.transmission_date = date
                    config.save_configuration({"message_count": self.lora.message_count, "transmission_date": date})

                # send 2, 3 or at most 4 messages per interval based on length of interval
                lora_slot = int(float(config.get_config("interval"))*60) // 30  # lora_rate changes for each 30 seconds
                if lora_slot < 2:
                    raise Exception("Interval has to be at least a minute")
                else:
                    lora_rate = lora_slot
                    if lora_slot > 4:
                        lora_rate = 4

                waiting = self.lora.lora_buffer.size(lora_rate)  # check how many messages are waiting (up to 4)
                remaining = self.lora.message_limit - self.lora.message_count  # check how many more we can send today
                if remaining <= 0:
                    self.logger.info("LoRa message limit reached for the day")
                if remaining - waiting >= 0:
                    count = waiting  # if we have more than we want to send, send them all
                else:
                    count = remaining  # if we have less than we want to send, send up to the limit
                for val in range(count):  # Schedule up to 4 randomly timed messages within interval
                    self.random_alarm = Timer.Alarm(self.random_event, s=self.get_random_time(), periodic=False)

        else:
            raise Exception("Non existent data type")

    def random_event(self, arg):
        # start LoRa thread
        arg1, arg2 = 0, 0  # threading library not fully implemented - only works with a tuple of at least 2 args
        _thread.start_new_thread(self.lora.lora_send, (arg1, arg2))

    def get_random_time(self):
        # get random number of seconds within interval, add one so it cannot be zero
        s_to_next_lora = int(machine.rng() / (2 ** 24) * int(float(config.get_config("interval"))*60)) + 1

        return s_to_next_lora
