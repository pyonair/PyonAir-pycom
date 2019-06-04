#!/usr/bin/env python
from Plantower import Plantower
import time

plantower = Plantower()

while (True):
    recv = plantower.read()
    if recv:
        print(recv)
        print()
    time.sleep(0.1)
