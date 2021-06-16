#!/usr/bin/python3

#********************************************************************
# Description:  solo_tool_changer
#               This file, 'solo_tool_changer.py', is a HAL component that 
#               has reads data from a D5 Next water cooler via
#               I2C.
#
# Author: John Allwine <john@pocketnc.com>
# License: GPL Version 2
#    
# Copyright (c) 2021 Pocket NC Company All rights reserved.
#
#*******************************************************************
import hal
import time
from state_machine import SoloToolChangerState, SAFE_Z, SAFE_X, EPS, B_MIN, B_MAX, X_MIN, X_MAX, Y_MIN, Y_MAX, Z_MIN
from tool_info import is_over_tool_slot

h = hal.component("solo-tool-changer")

# used to open the tool changer
h.newpin("open-cmd", hal.HAL_BIT, hal.HAL_IN)

# used to allow everything to initialize before enabling
h.newpin("enabled", hal.HAL_BIT, hal.HAL_IN)

# pin for user to indicate it's safe to close tool changer when machine is not homed
h.newpin("safe-to-close", hal.HAL_BIT, hal.HAL_IN)

# inputs for making decisions about opening and closing the tool changer
# when override is false
h.newpin("x-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("x-homed", hal.HAL_BIT, hal.HAL_IN)
h.newpin("y-homed", hal.HAL_BIT, hal.HAL_IN)
h.newpin("z-homed", hal.HAL_BIT, hal.HAL_IN)
h.newpin("b-homed", hal.HAL_BIT, hal.HAL_IN)
h.newpin("closed-sensor", hal.HAL_BIT, hal.HAL_IN)
h.newpin("opened-sensor", hal.HAL_BIT, hal.HAL_IN)

# outputs for controlling open/close solenoid
h.newpin("open-out", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("close-out", hal.HAL_BIT, hal.HAL_OUT)

# outputs for disabling homing and feed under certain conditions
h.newpin("inhibit-feed", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("inhibit-homing", hal.HAL_BIT, hal.HAL_OUT)

# outputs for signaling a tool changer fault
h.newpin("fault", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("fault-reason", hal.HAL_S32, hal.HAL_OUT)

# limits which change when the drawer is open to avoid collisions
h.newpin("b-max", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("b-min", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("z-min", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("x-max", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("x-min", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("y-max", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("y-min", hal.HAL_FLOAT, hal.HAL_OUT)

# debugging pin to show the internal state machine state
h.newpin("state", hal.HAL_S32, hal.HAL_OUT)
h.ready()

pollTime = .2

h["open-cmd"] = False
h["enabled"] = False

# default to input that would be considered a fault
h["closed-sensor"] = False
h["opened-sensor"] = False
h["b-position"] = -90
h["x-position"] = 4.5
h["y-position"] = 0
h["z-position"] = -6
h["b-max"] = B_MAX
h["b-min"] = B_MIN
h["x-max"] = X_MAX
h["x-min"] = X_MIN
h["y-max"] = Y_MAX
h["y-min"] = Y_MIN
h["z-min"] = Z_MIN 

h["x-homed"] = False
h["y-homed"] = False
h["z-homed"] = False
h["b-homed"] = False

# default to not driving the air solenoids and inhibit machine
# movement until we make a determination about what state the
# machine is in
h["open-out"] = False
h["close-out"] =  False
h["inhibit-feed"] = False
h["inhibit-homing"] = True

# default to not a fault condition, which will change 
# if improperly wired up or machine is in fault state
h["fault"] = False
h["fault-reason"] = False

# state for ensuring drawer safely opens and closes
# also limits ability to home if the drawer isn't closed
state = SoloToolChangerState(h)

try:
  while not h["enabled"]: 
    pass
    
  while True:
    state.next()
    state.incrementTime(pollTime)

# helps prevent accidental collisions when tool changer drawer is open
    if (
      not h["closed-sensor"] and 
      h["x-homed"] and
      h["y-homed"] and
      h["z-homed"] and
      h["b-homed"]
    ):
      # Drawer isn't closed and axes are homed

      if h["x-position"] <= SAFE_X+EPS:
        # Spindle not over tool changing drawer, full Z movement OK
        h["z-min"] = Z_MIN-EPS

        if h["z-position"] <= SAFE_Z+EPS:
          # Z is lower than is safe when over the drawer, so limit X
          h["x-max"] = SAFE_X+EPS
        else:
          # Z is at safe height to be over drawer, so allow full X movement
          h["x-max"] = X_MAX
      else:
        # Spindle is over open tool changer drawer
        if is_over_tool_slot(h["x-position"], h["y-position"]):
          pass
      
    time.sleep(pollTime)

    while not h["enabled"]:
      pass
except KeyboardInterrupt:
  raise SystemExit
