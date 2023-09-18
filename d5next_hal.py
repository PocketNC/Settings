#!/usr/bin/python3

#********************************************************************
# Description:  d5next_hal.py
#               This file, 'd5next_hal.py', is a HAL component that 
#               reads data from a D5 Next water cooler via I2C.
#
# Author: John Allwine <john@pocketnc.com>
# License: GPL Version 2
#    
# Copyright (c) 2023 Pocket NC Company All rights reserved.
#
#*******************************************************************

import d5next
import sys
import hal
import time

name = sys.argv[1] if len(sys.argv) > 1 else "d5next"
address = int(sys.argv[2]) if len(sys.argv) > 2 else 0x1e

h = hal.component(name)

h.newpin("fan.output", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.current", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.speed", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.flags", hal.HAL_FLOAT, hal.HAL_OUT)

h.newpin("pump.output", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.current", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.speed", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.flags", hal.HAL_FLOAT, hal.HAL_OUT)

h.newpin("flow", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("temperature_c", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("temperature_f", hal.HAL_FLOAT, hal.HAL_OUT)

h.newpin("error", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

device = d5next.D5Next(address)

try:
  while True:
    try:
      device.readData()
      h['fan.output'] = device.fan_output
      h['fan.voltage'] = device.fan_voltage
      h['fan.current'] = device.fan_current
      h['fan.speed'] = device.fan_speed
      h['fan.flags'] = device.fan_flags

      h['pump.output'] = device.pump_output
      h['pump.voltage'] = device.pump_voltage
      h['pump.current'] = device.pump_current
      h['pump.speed'] = device.pump_speed
      h['pump.flags'] = device.pump_flags

      h['flow'] = device.flow
      h['temperature_c'] = device.temperature_c
      h['temperature_f'] = device.temperature_f
      h['error'] = 0
    except d5next.D5NextCommunicationError:
      h['error'] = 1
    except d5next.D5NextInvalidDataError:
      h['error'] = 2

    time.sleep(1)
except KeyboardInterrupt:
  raise SystemExit


