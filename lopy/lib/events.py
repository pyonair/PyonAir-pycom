import machine
from machine import RTC, Timer
from tasks import flash_pm_averages
import _thread
from LoRa_thread import lora_thread


class EventScheduler:
    def __init__(self, avg_interval, rtc, sensor_name, logger):

        self.avg_interval_s = avg_interval
        self.rtc = rtc
        self.logger = logger
        self.sensor_name = sensor_name
        self.s_to_next_lora = None
        self.logger = logger

        self.count = 1
        self.now = rtc.now()
        self.next_event_s = self.avg_interval_s - (
                    ((self.now[3] * 3600) + (
                     self.now[4] * 60) + self.now[5] + (self.now[6]) / 1000000) % self.avg_interval_s)
        self.periodic_average_event = None
        self.random_lora_event = None
        self.first_event = Timer.Alarm(self.set_event_queue, s=self.next_event_s, periodic=False)

    def set_event_queue(self, arg):
        self.periodic_average_event = Timer.Alarm(self.get_averages, s=self.avg_interval_s, periodic=True)
        self.get_averages(arg)

    def get_averages(self, arg):
        self.logger.info("Running flash_pm_averages task")
        flash_pm_averages(sensor_name=self.sensor_name, logger=self.logger)
        self.s_to_next_lora = int(machine.rng() / (2**24) * self.avg_interval_s)
        self.random_lora_event = Timer.Alarm(self.send_over_lora, s=self.s_to_next_lora, periodic=False)

    def send_over_lora(self, arg):
        self.logger.info("Sending data over LoRaWAN")
        _thread.start_new_thread(lora_thread, ('LoRa_send', "PM1.csv.tosend", self.logger, 30))
