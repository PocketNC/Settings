#!/usr/bin/python3

from IrDA_Probe_I2C import IrDA_Probe_I2C
from i2c import busNum
import hal
import time

address = 0x44

probe = IrDA_Probe_I2C(address, busNum)

h = hal.component("solo-probe")

# pressure is a float from 0-1 that represents a parameter between minimum and maximum pressure
h.newpin("probe-on", hal.HAL_BIT, hal.HAL_IN)

h.ready()

lastProbeOn = False
try:
  while True:
    try:
      if h["probe-on"] != lastProbeOn:
        if h["probe-on"]:
          # Probe was commanded to turn on
          probe.wake()
        else:
          # Probe was commanded to turn off
          probe.sleep()

      lastProbeOn = h["probe-on"]
    except:
      pass

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

