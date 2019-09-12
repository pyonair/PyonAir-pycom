# Helper functions and miscellaneous globals

from Configuration import config
import strings as s
import time
import pycom
import _thread


# locks/mutexes
current_lock = _thread.allocate_lock()
wifi_lock = _thread.allocate_lock()
lora_lock = _thread.allocate_lock()
led_lock = _thread.allocate_lock()


def seconds_to_first_event(interval_s):
    """
    Computes number of seconds (float) until the first sensor average reading
    :param rtc: real time clock object containing current time up to microsecond precision
    :param interval_s: interval between average readings
    :type interval_s: int
    :return:  number of seconds until first event
    """
    current_time = time.gmtime()
    first_event_s = interval_s - (((current_time[3] * 60 * 60) + (current_time[4] * 60) + current_time[5]) % interval_s)

    return first_event_s


def minutes_of_the_month():
    """
    :return: Number of seconds from the start of the month
    :rtype: int
    """
    t = time.gmtime()
    days, hours, minutes = t[2], t[3], t[4]
    return ((days - 1) * 24 * 60) + (hours * 60) + minutes


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


def blink_led(args):

    colour, delay, blocking = args[0], args[1], args[2]

    if blocking:
        acquired = False
        re_tries = 0
        while not acquired:  # pycom has not yet implemented the timeout feature
            acquired = led_lock.acquire(0)
            time.sleep(0.1)
            re_tries += 1
            if re_tries >= 6:
                break
    else:
        # acquired = led_lock.acquire(0)
        acquired = not led_lock.locked()

    if acquired:
        pycom.rgbled(colour)
        time.sleep(delay)
        pycom.rgbled(0x000000)
        if blocking:
            led_lock.release()


# returns a dictionary of sensors and if they are enabled
def get_sensors():

    sensors = {s.TEMP: False, s.PM1: False, s.PM2: False}

    for sensor in sensors:
        if config.get_config(sensor) != "OFF":
            sensors[sensor] = True

    return sensors


def get_format(sensors):

    fmt = ""
    for sensor_name in [s.TEMP, s.PM1, s.PM2]:
        if sensors[sensor_name]:  # if the sensor is enabled
            fmt += sensor_name[0]  # add the first character to fmt to construct format eg.: TPP, TP, PP, P, T

    return fmt
