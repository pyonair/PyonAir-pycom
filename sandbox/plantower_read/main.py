#!/usr/bin/env python
from Plantower import Plantower
import time

plantower = Plantower()

while (True):
    plantower.read()
    time.sleep(0.05)
