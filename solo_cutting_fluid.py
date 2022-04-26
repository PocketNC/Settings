#!/usr/bin/python3

from i2c import bus

import hal
import time

h = hal.component("solo_cutting_fluid")

# pressure is a float from 0-1 that represents a parameter between minimum and maximum pressure
h.newpin("pressure", hal.HAL_FLOAT, hal.HAL_IN)
h.ready()

lastPressure = 1

try:
  while True:
    if h['pressure'] != lastPressure:
      t = max(min(h['pressure'], 1), 0)

      lastPressure = t

      i = int(1843*(1-t)+t*4095)
      lo = i & 15 << 4
      hi = i >> 4
      combined = (lo << 8) | hi
      try:
        bus.write_word_data(0x60, 64, combined)
      except:
        print("Failed to set pressure")

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

