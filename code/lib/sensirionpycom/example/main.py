"""
Example programme that runs on a Pycom board and prints sensirion readings.
Peter Varga
06/08/2019

Place this file in your main project folder, so that the project structure is as follows:
Your-project-folder
|-lib
  |-sensirionpycom
    |-__init__.py
    |-logging.py
    |-sensirion.py
|-main.py
"""

from sensirionpycom import Sensirion
from time import sleep

RX_DELAY_S = 1
LOOP_DELAY_S = 1  # cannot poll new reading within one second

SPS030 = Sensirion()  # automatically starts measurement
sleep(RX_DELAY_S)  # wait for sensor to initialize

while True:  # start reading measurements
    data = SPS030.read()
    print(data)
    sleep(LOOP_DELAY_S)
