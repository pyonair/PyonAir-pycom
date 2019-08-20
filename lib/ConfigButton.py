from machine import Timer
from new_config import new_config
import _thread


class ConfigButton:
    def __init__(self, logger):

        self.logger = logger
        self.debounce_timer = Timer.Chrono()
        self.debounce_timer.start()
        self.button_held = Timer.Alarm(None, s=2.5)

    def button_handler(self, pin):
        if self.debounce_timer.read_ms() >= 10:  # 10 ms software switch debounce
            self.debounce_timer.reset()
            value = pin.value()
            if value == 0:  # Button pressed
                self.button_held = Timer.Alarm(self.start_config, s=2.5, periodic=False)
            elif value == 1:  # Button released
                self.button_held.cancel()

    def start_config(self, arg):  # this handler is called when button was held for 2.5 sec
        _thread.start_new_thread(new_config, (self.logger, 300))
