"""
Example programme that runs on a Pycom board and prints plantower readings.
Daniel Hausner
20/06/2019

Place this file in your main project folder, so that the project structure is as follows:
Your-project-folder
|-lib
  |-plantowerpycom
    |-__init__.py
    |-logging.py
    |-plantower.py
|-main.py
"""

from plantowerpycom import Plantower, PlantowerException
from machine import RTC

plantower = Plantower()

# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # Pass time tuple (e.g. from GPS) to initialise the time

while True:
    try:
        recv = plantower.read()
        print(recv)
    except PlantowerException as pe:
        print(pe)