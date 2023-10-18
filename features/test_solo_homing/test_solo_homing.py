#!/usr/bin/python3

import hal
import time
import ini
import os

POCKETNC_VAR_DIRECTORY = os.environ["POCKETNC_VAR_DIRECTORY"]

INI = ini.read_ini_data(os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini"))

X_HOME_OFFSET = float(ini.get_parameter(INI, "JOINT_0", "HOME_OFFSET")['values']['value'])
Y_HOME_OFFSET = float(ini.get_parameter(INI, "JOINT_1", "HOME_OFFSET")['values']['value'])
Z_HOME_OFFSET = float(ini.get_parameter(INI, "JOINT_2", "HOME_OFFSET")['values']['value'])
B_HOME_OFFSET = float(ini.get_parameter(INI, "JOINT_3", "HOME_OFFSET")['values']['value'])
C_HOME_OFFSET = float(ini.get_parameter(INI, "JOINT_4", "HOME_OFFSET")['values']['value'])

h = hal.component("test-solo-homing")

h.newpin("x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("c", hal.HAL_FLOAT, hal.HAL_IN)

h.newpin("x-limit", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("y-limit", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("z-limit", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("b-limit", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("b-index", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("c-limit", hal.HAL_BIT, hal.HAL_OUT)

h.ready()

try:
  while True:
    h["x-limit"] = h["x"] <= X_HOME_OFFSET
    h["y-limit"] = h["y"] >= Y_HOME_OFFSET
    h["z-limit"] = h["z"] >= Z_HOME_OFFSET
    h["b-limit"] = h["b"] <= B_HOME_OFFSET
    h["b-index"] = (h["b"]%1) < .01
    h["c-limit"] = h["c"] <= C_HOME_OFFSET
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit

