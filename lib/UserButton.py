from machine import Timer, reset
from new_config import new_config
import _thread


class UserButton:
    def __init__(self, logger):

        self.logger = logger
        self.debounce_timer = Timer.Chrono()
        self.debounce_timer.start()
        self.reboot_timer = Timer.Chrono()
        self.reboot_timer.start()
        self.config_press = False
        self.config_enabled = False
        self.config_blocking = True
        self.config_start = False
        self.reboot = True

    def button_handler(self, pin):
        if self.debounce_timer.read_ms() >= 10:  # 10 ms software switch debounce
            self.debounce_timer.reset()
            value = pin.value()
            if value == 1:  # Button pressed
                if self.config_enabled:
                    self.config_press = Timer.Alarm(self.start_config, s=2.5, periodic=False)
                self.reboot_timer.reset()

            elif value == 0:  # Button released

                # Cancel alarm to enter config, since button was not held for 2.5 seconds continuously
                if self.config_press is not False:
                    self.config_press.cancel()

                # If button was pressed and released within 1.5 seconds, then reboot the device
                if self.reboot_timer.read() < 1.5:
                    try:  # if sd card failed to mount handle exception thrown in logger
                        self.logger.info("Button press - rebooting...")
                    except Exception as e:
                        pass
                    reset()

    # this handler is called when button was held for 2.5 sec
    def start_config(self, arg):
        # arg is a dummy argument, because _thread.start_new_thread only takes tuples with at least 2 values

        # If button is pressed upon exception in the main do not automatically reboot, instead, block execution and
        # enter configurations
        self.reboot = False

        # config_blocking is True by default, and set False in main once all critical failures were dealt with
        if not self.config_blocking:  # Configurations are entered parallel to main execution
            _thread.start_new_thread(new_config, (self.logger, arg))

    def get_reboot(self):
        return self.reboot

    def set_config_blocking(self, config_blocking):
        self.config_blocking = config_blocking

    def set_config_enabled(self, config_enabled):
        self.config_enabled = config_enabled
