#!/usr/bin/env python
from Plantower import Plantower, PlantowerException
import time

plantower = Plantower()

while (True):
    try:
        recv = plantower.read()
        if recv:
            print(recv)
            print()
    except PlantowerException as pe:
        print(pe)
    time.sleep(0.1)
