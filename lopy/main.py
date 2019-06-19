#!/usr/bin/env python
from plantower import Plantower, PlantowerException
import time
from sd_card import SDCard
from machine import RTC, Timer
from strings import sensor_logfile_template, timestamp_template
from helper import mean_across_arrays

# Setting
loop_time = 0.1  # delay between the sensor readings (seconds)

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: get time from GPS
now = rtc.now()

# Initialise SD card
sd = SDCard(
    rtc=rtc,
    sensor_logfile=sensor_logfile_template.format(*now),
    status_logfile='status_log.txt',
    debug=True
)

# Global variables for sensor reading and computing averages
plantower = Plantower()
last_timestamp = None
sensor_readings_lst = []

# Chronometer for timing the loop execution
chrono = Timer.Chrono()
chrono.start()
while True:

    try:
        recv = plantower.read()
        if recv:
            print(recv)
            print()
            recv_lst = str(recv).split(',')
            curr_timestamp = recv_lst[0]
            sensor_reading = [int(i) for i in recv_lst[1:]]
            if curr_timestamp != last_timestamp:
                # If there are any readings with the previous timestamps, process them
                if len(sensor_readings_lst) > 0:
                    lst_to_log = [last_timestamp] + [str(i) for i in mean_across_arrays(sensor_readings_lst)]
                    line_to_log = ','.join(lst_to_log)
                    sd.log_sensor_line(line_to_log)
                # Set/reset global variables
                last_timestamp = curr_timestamp
                sensor_readings_lst = []
            # Add the current reading to the list, which will be processed when the timestamp changes
            sensor_readings_lst.append(sensor_reading)

    except PlantowerException as e:
        status_line = ', '.join([timestamp_template.format(*rtc.now()), str(e.__class__)])
        print(status_line)
        # TODO: log exception

    finally:
        elapsed = chrono.read()
        if elapsed < loop_time:
            time.sleep(loop_time - elapsed)
        # TODO: raise warning if the elapsed time is loner than the loop_time
        chrono.reset()

# TODO: take mean of the messages if two or more readings per second
