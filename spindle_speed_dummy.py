#!/usr/bin/python

import hal
import time

h = hal.component("spindle_speed")
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_measured", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

h['speed_measured'] = 0

try:
  while True:
    time.sleep(100000)
except KeyboardInterrupt:
  raise SystemExit
