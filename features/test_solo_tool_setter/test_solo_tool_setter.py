#!/usr/bin/python3

import hal
import time

h = hal.component("test-solo-tool-setter")

h.newpin("x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("trigger-x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("trigger-y", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("trigger-z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("trigger-b", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("tool-offset", hal.HAL_FLOAT, hal.HAL_IN)

h.newpin("probe-output", hal.HAL_BIT, hal.HAL_OUT)

h.ready()

try:
  while True:
    dx = h["x"]-h["trigger-x"]
    dy = h["y"]-h["trigger-y"]
    dz = (h["z"] - h["tool-offset"]) - h["trigger-z"]
    db = h["b"]-h["trigger-b"]
    h["probe-output"] = abs(dx) < .0001 and abs(dy) < .0001 and dz < .000001 and abs(db) < .001
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit

