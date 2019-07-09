from machine import Timer
from configuration import config_thread
import _thread


class ButtonPress:
    def __init__(self, logger):

        self.logger = logger
        self.Press = True
        self.debounce_timer = Timer.Chrono()
        self.debounce_timer.start()
        self.button_held = None

    def press_handler(self, arg):
        if self.debounce_timer.read_ms() >= 10:  # 10 ms software switch debounce
            self.debounce_timer.reset()
            if self.Press:
                self.button_held = Timer.Alarm(self.start_config, 3, periodic=False)
            else:
                self.button_held.cancel()
            self.Press = not self.Press

    def start_config(self, arg):  # this handler is called when button was held for 3 sec
        _thread.start_new_thread(config_thread, ('Config', self.logger, 300))
