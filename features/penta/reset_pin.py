#!/usr/bin/python3

import time
import hal
import sys

if __name__ == "__main__":
  h = hal.component(sys.argv[1])
  h.newpin("value", hal.HAL_BIT, hal.HAL_IN)
  h.newpin("in", hal.HAL_BIT, hal.HAL_IO)
  h.newpin("out", hal.HAL_BIT, hal.HAL_OUT)
  h.newpin("delay", hal.HAL_FLOAT, hal.HAL_IN)
  h.ready()

  h["delay"] = .1

  try:
    while True:
      if h["in"] != h["value"]:
        h["out"] = h["in"]
        time.sleep(h["delay"])
        h["in"] = h["value"]
        h["out"] = h["value"]

      time.sleep(.1)
  except KeyboardInterrupt:
    raise SystemExit
