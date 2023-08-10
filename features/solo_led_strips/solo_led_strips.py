#!/usr/bin/python3

from SoloLEDStrip import SoloLEDStrip
from i2c import busNum

import hal
import time

LEDs = SoloLEDStrip()

h = hal.component("solo-led-strips")

h.newpin("status", hal.HAL_S32, hal.HAL_IN)

h.ready()

lastStatus = 0

def normal():
  LEDs.normal()

def error():
  LEDs.error()

def success():
  LEDs.success()

def party():
  LEDs.party()

commands = [ normal, error, success, party ]

try:
  while True:
    if h['status'] != lastStatus:
      lastStatus = h['status']

      if h['status'] >= 0 and h['status'] < len(commands):
        commands[h['status']]()

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

