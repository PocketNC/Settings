#!/usr/bin/python

import hal

h = hal.component("spindle_voltage")
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_measured", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

h['speed_measured'] = 0
