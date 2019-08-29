import machine
from machine import RTC, Timer
from tasks import flash_pm_averages, send_over_lora
from helper import seconds_to_first_event
from Configuration import config
from math import ceil
import GpsSIM28
import _thread


class EventScheduler:
    def __init__(self, rtc, logger, event_type, lora, lora_socket):

        #  Arguments
        self.rtc = rtc
        self.logger = logger
        self.event_type = event_type
        self.lora = lora
        self.lora_socket = lora_socket

        #  Attributes
        if self.event_type == "PM":
            self.interval_s = int(float(config.get_config("PM_interval"))*60)
        elif self.event_type == "GPS":
            self.interval_s = int(float(config.get_config("GPS_freq"))*3600)
        self.s_to_next_lora = None
        self.first_alarm = None
        self.periodic_alarm = None
        self.random_alarm = None

        #  Start scheduling events
        self.set_event_queue()

    #  Calculates time (s) until the first event, and sets up an alarm
    def set_event_queue(self):
        first_event_s = seconds_to_first_event(self.rtc, self.interval_s)
        self.first_alarm = Timer.Alarm(self.first_event, s=first_event_s, periodic=False)

    def first_event(self, arg):
        #  set up periodic alarm with specified interval to calculate averages
        self.periodic_alarm = Timer.Alarm(self.periodic_event, s=self.interval_s, periodic=True)
        self.periodic_event(arg)

    def periodic_event(self, arg):

        if self.event_type == "PM":

            #  flash averages of PM data to sd card to be sent over LoRa
            flash_pm_averages(logger=self.logger)

            """get random number of seconds within interval, subtracting the timeout, leaving 5 seconds leeway, and add
            one so it cannot be zero"""
            self.s_to_next_lora = int(machine.rng() / (2 ** 24) * (int(float(config.get_config("PM_interval")) * 60) -
                                                                   (int(config.get_config("lora_timeout")) + 5))) + 1
        elif self.event_type == "GPS":

            #  get position from gps to be sent over LoRA
            _thread.start_new_thread(GpsSIM28.get_position, (self.logger, arg))

            """get random number of seconds within interval, subtracting the timeout, leaving 5 seconds leeway, and add
            gps timeout so LoRa cannot start before GPS has acquired position"""
            self.s_to_next_lora = int(machine.rng() / (2**24) * (int(float(config.get_config("PM_interval"))*60) -
                (int(config.get_config("lora_timeout")) + 5))) + ceil((int(float(config.get_config("GPS_timeout")))))

        #  set up an alarm with random delay to send data over LoRa
        self.random_alarm = Timer.Alarm(self.random_event, s=self.s_to_next_lora, periodic=False)

    def random_event(self, arg):
        if self.event_type == "PM":
            send_over_lora(logger=self.logger, data_type="PM", lora=self.lora, lora_socket=self.lora_socket)
        elif self.event_type == "GPS":
            send_over_lora(logger=self.logger, data_type="GPS", lora=self.lora, lora_socket=self.lora_socket)
