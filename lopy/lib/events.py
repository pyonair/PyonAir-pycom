import machine
from machine import RTC, Timer
from tasks import flash_pm_averages


class EventScheduler:
    def __init__(self, interval_ms, rtc, sensor_name, logger):

        self.interval_ms = interval_ms
        self.rtc = rtc
        self.logger = logger
        self.sensor_name = sensor_name
        self.ms_to_next_lora = None

        self.now = rtc.now()
        self.next_event_ms = self.interval_ms - (
                    ((int(self.now[3]) * 3600000) + (int(
                     self.now[4]) * 60000) + (int(self.now[5]) * 1000) + (int(self.now[6]) // 1000)) % self.interval_ms)

        self.periodic_average_event = None
        self.random_lora_event = None
        self.first_event = Timer.Alarm(self.set_event_queue, ms=self.next_event_ms, periodic=False)

    def set_event_queue(self, arg):
        self.periodic_average_event = Timer.Alarm(self.get_averages, ms=self.interval_ms, periodic=True)
        # print(self.rtc.now(), "Event queue was set")
        self.get_averages(arg)

    def get_averages(self, arg):
        self.logger.info("Running flash_pm_averages task")
        flash_pm_averages(sensor_name=self.sensor_name, logger=self.logger)
        self.ms_to_next_lora = int(machine.rng() / (2**24) * self.interval_ms)
        self.random_lora_event = Timer.Alarm(self.send_over_lora, ms=self.ms_to_next_lora, periodic=False)

    def send_over_lora(self, arg):
        self.logger.info("Sending data over LoRaWAN")
        # ToDo: Replace with code that sends data over LoRa
