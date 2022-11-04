#!/usr/bin/python3

import time
import hal
import sys

if __name__ == "__main__":
  h = hal.component(sys.argv[1])
  h.newpin("value", hal.HAL_BIT, hal.HAL_IN)
  h.newpin("pin", hal.HAL_BIT, hal.HAL_IO)
  h.ready()

  try:
    while True:
      h["pin"] = h["value"]
      time.sleep(.1)
  except KeyboardInterrupt:
    raise SystemExit
