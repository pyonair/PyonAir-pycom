# Helper functions

from Configuration import config
from loggingpycom import INFO, WARNING, CRITICAL, DEBUG, ERROR
import time
import pycom
import _thread

current_lock = _thread.allocate_lock()
processing_lock = _thread.allocate_lock()
archive_lock = _thread.allocate_lock()
tosend_lock = _thread.allocate_lock()
led_lock = _thread.allocate_lock()


def seconds_to_first_event(rtc, interval_s):
    """
    Computes number of seconds (float) until the first sensor average reading
    :param rtc: real time clock object containing current time up to microsecond precision
    :param interval_s: interval between average readings
    :type interval_s: int
    :return:  number of seconds until first event
    """
    now = rtc.now()
    first_event_s = interval_s - (((now[4] * 60) + now[5] + (now[6]) / 1000000) % interval_s)
    hours = interval_s // 3600
    if hours >= 1:
        first_event_s += hours * 3600
    return first_event_s


def minutes_from_midnight():
    """

    :return: Number of seconds from midnight
    :rtype: int
    """
    t = time.gmtime()
    hours, minutes = t[3], t[4]
    return (hours * 60) + minutes


def mean_across_arrays(arrays):
    """
    Computes elementwise mean across arrays.
    E.g. for input [[1, 2, 4], [5, 3, 6]] returns [3, 2.5, 5]
    :param arrays: list of arrays of the same length
    :return: elementwise average across arrays
    """
    out_arr = []
    n_arrays = len(arrays)
    # Iterate through the elements in an array
    for i in range(len(arrays[0])):
        sm = 0
        # Iterate through all the arrays
        for array in arrays:
            sm += array[i]
        out_arr.append(sm/n_arrays)
    return out_arr


def get_logging_level():
    logging_lvl = config.get_config("logging_lvl")
    if logging_lvl == "Critical":
        return CRITICAL
    elif logging_lvl == "Error":
        return ERROR
    elif logging_lvl == "Warning":
        return WARNING
    elif logging_lvl == "Info":
        return INFO
    elif logging_lvl == "Debug":
        return DEBUG


def blink_led(colour=0x770000, count=1, delay=0.4, blocking=False):
    """
    Blink with the inbuilt LED
    :param colour: colour in format like 0x770000, which is red
    :type colour: int
    :param count: number of blinks
    :type count: int
    :param delay: delay in between blinks in seconds
    :type delay: float
    :param blocking: True - will execute even if it has to wait, False - does not execute if LED is already in use
    :type blocking: bool
    """

    if blocking:
        acquired = False
        re_tries = 0
        while not acquired:  # pycom has not yet implemented the timeout feature
            acquired = led_lock.acquire(0)
            time.sleep(0.2)
            re_tries += 1
            if re_tries >= 7:
                break
    else:
        acquired = led_lock.acquire(0)

    if acquired:
        for i in range(count):
            pycom.rgbled(colour)
            time.sleep(delay)
            pycom.rgbled(0x000000)
            time.sleep(delay)

        led_lock.release()


# yellow blink to simulate heartbeat
def heartbeat(arg):
    blink_led(colour=0x005500, count=1, delay=0.1, blocking=True)

