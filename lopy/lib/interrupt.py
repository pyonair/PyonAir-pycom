from machine import Timer
from configuration import config_thread
import _thread


class ButtonPress:
    def __init__(self, sd):

        self.sd = sd
        self.Press = True
        self.debounce_timer = Timer.Chrono()
        self.debounce_timer.start()
        self.button_held = None

    def press_handler(self, arg):
        if self.debounce_timer.read_ms() >= 10:  # 10 ms software switch debounce
            self.debounce_timer.reset()
            if self.Press:
                #  print('Pressed')
                self.button_held = Timer.Alarm(self.held_handler, 3, periodic=False)
            else:
                #  print('Released')
                self.button_held.cancel()
            self.Press = not self.Press

    def held_handler(self, arg):  # this handler is called when button was held for 3 sec
        _thread.start_new_thread(config_thread, (self.sd, 'Config'))
