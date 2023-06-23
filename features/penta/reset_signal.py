#!/usr/bin/python3

import time
import hal
import sys
import machinekit.hal

if __name__ == "__main__":
  name = sys.argv[1]
  h = hal.component(name)
  h.newpin("value", hal.HAL_BIT, hal.HAL_IN)
  h.newpin("in", hal.HAL_BIT, hal.HAL_IN)
  h.newpin("out", hal.HAL_BIT, hal.HAL_OUT)
  h.newpin("delay", hal.HAL_FLOAT, hal.HAL_IN)
  h.newpin("enable", hal.HAL_BIT, hal.HAL_IN)

  h["delay"] = .1
  h["value"] = 0
  h["enable"] = 0 # enable once the signal has been created

  h.ready()

  try:
    while not h["enable"]:
      time.sleep(.1)

    signal = machinekit.hal.Signal(name)

    while True:
      if h["in"] != h["value"]:
        h["out"] = h["in"]
        time.sleep(h["delay"])
        signal.set(h["value"])

      h["out"] = h["in"]
      time.sleep(.1)
  except KeyboardInterrupt:
    raise SystemExit
