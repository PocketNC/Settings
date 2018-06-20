#!/usr/bin/python

from Adafruit_I2C import Adafruit_I2C
import hal
import time

i2c = Adafruit_I2C(0x60)

h = hal.component("spindle_voltage")
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.ready()

x0 = 200.0
y0 = 764.15

x1 = 2080.0
y1 = 10000.0

lastSpeed = 0

try:
  while True:
    if h['speed_in'] != lastSpeed:
      speed = h['speed_in']
      value = x0+(x1-x0)*(speed-y0)/(y1-y0) 

      i = int(min(max(value, 0), 4095))

      lo = i & 15 << 4
      hi = i >> 4

      combined = (lo << 8) | hi

      i2c.write16(64, combined)
      lastSpeed = speed

  time.sleep(1)
except KeyboardInterrupt:
  raise SystemExit

