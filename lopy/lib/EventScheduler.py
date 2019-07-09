import machine
from machine import RTC, Timer
from tasks import flash_pm_averages, send_over_lora
from helper import seconds_to_first_event


class EventScheduler:
    def __init__(self, interval_s, rtc, sensor_name, logger):

        #  Arguments
        self.interval_s = interval_s
        self.rtc = rtc
        self.logger = logger
        self.sensor_name = sensor_name

        #  Attributes
        self.s_to_next_lora = None
        self.first_alarm = None
        self.periodic_alarm = None
        self.random_alarm = None

        #  Start scheduling events
        self.set_event_queue()

    #  Calculates time (s) until the first event, and sets up an alarm
    def set_event_queue(self):
        #  process and send previous data immediately upon boot
        flash_pm_averages(sensor_name=self.sensor_name, logger=self.logger)
        send_over_lora(sensor_name=self.sensor_name, logger=self.logger, timeout=60)
        first_event_s = seconds_to_first_event(self.rtc, self.interval_s)
        self.first_alarm = Timer.Alarm(self.first_event, s=first_event_s, periodic=False)

    def first_event(self, arg):
        #  set up periodic alarm with specified interval to calculate averages
        self.periodic_alarm = Timer.Alarm(self.periodic_event, s=self.interval_s, periodic=True)
        self.periodic_event(arg)

    def periodic_event(self, arg):
        self.logger.info("Running flash_pm_averages task")

        #  flash averages of data to sd card at the end of the interval
        flash_pm_averages(sensor_name=self.sensor_name, logger=self.logger)

        #  get random number of seconds within interval
        self.s_to_next_lora = int(machine.rng() / (2**24) * self.interval_s)

        #  set up an alarm with random delay to send data over LoRa
        self.random_alarm = Timer.Alarm(self.random_event, s=self.s_to_next_lora, periodic=False)

    def random_event(self, arg):
        send_over_lora(sensor_name=self.sensor_name, logger=self.logger, timeout=60)
