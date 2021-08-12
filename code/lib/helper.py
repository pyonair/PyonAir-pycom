# Helper functions and miscellaneous globals

from Configuration import Configuration #import config
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
    Computes number of seconds (float) until the first sensor average reading, such that the event will occur at a
    second divisible by the interval
    :param interval_s: int
    :type interval_s: int
    :return: seconds until the first event
    :rtype: float
    """
    current_time = time.gmtime()
    first_event_s = interval_s - (((current_time[3] * 60 * 60) + (current_time[4] * 60) + current_time[5]) % interval_s)

    return first_event_s


def secOfTheMonth():
    """
    :return: Number of SECONDS from the start of the month
    :rtype: int
    """
    t = time.gmtime()
    #print(t)
    days, hours, minutes,sec = t[2] -1, t[3], t[4], t[5]

    #sec in day = 24 x 60 x 60 = 86400
    #sec in hour = 60 X 60 = 3600

    secInt = (days  * 86400) + (hours * 3600) + (minutes * 60) + sec
    #print (minInt)
    return secInt


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
    """
    Schedule a blink on the LED of a given colour for a given time. If blocking is set True, it will wait until lock
    is acquired or timed out. If blocking is False, it will take the lock if it is free, pass otherwise
    :param args: colour, delay, blocking
    :type args: tuple(hex, int, bool)
    """
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
def get_sensors(config, logger):
    """
    Dictionary of sensors (TEMP, PM1, PM2) and whether they are enabled in the configurations
    :return: sensors
    :rtype: dict
    """
    sensors = {s.TEMP: False, s.PM1: False, s.PM2: False}

    for sensor in sensors:
        if config.get_config(sensor) != "OFF":
            sensors[sensor] = True

    return sensors


def get_format(sensors):
    """
    Constructs a format based on the type of sensors that are enabled
    :param sensors: Dictionary of sensors (TEMP, PM1, PM2) and whether they are enabled in the configurations
    :type sensors: dict
    :return: format
    :rtype: str
    """
    fmt = ""
    for sensor_name in [s.TEMP, s.PM1, s.PM2]:
        if sensors[sensor_name]:  # if the sensor is enabled
            fmt += sensor_name[0]  # add the first character to fmt to construct format eg.: TPP, TP, PP, P, T

    return fmt
