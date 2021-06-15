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
from state_machine import SoloToolChangerState

h = hal.component("solo-tool-changer")

## set true to override outputs
#h.newpin("override", hal.HAL_BIT, hal.HAL_IN)
#
## when override is true, outputs are set with these pins
#h.newpin("override-open", hal.HAL_BIT, hal.HAL_IN)
#h.newpin("override-close", hal.HAL_BIT, hal.HAL_IN)
#h.newpin("override-inhibit-feed", hal.HAL_BIT, hal.HAL_IN)
#h.newpin("override-inhibit-homing", hal.HAL_BIT, hal.HAL_IN)
#
## control for opening and closing tool changer
## when override is false

# used to open the tool changer via a program
h.newpin("open-cmd", hal.HAL_BIT, hal.HAL_IN)

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

# the minimum B limit, which changes when the door is open to avoid collisions
h.newpin("b-min", hal.HAL_FLOAT, hal.HAL_OUT)

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
h["b-min"] = -135

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

state = SoloToolChangerState(h)

try:
  while not h["enabled"]: 
    pass
    
  while True:
    state.next()
    state.incrementTime(pollTime)
    time.sleep(pollTime)

    while not h["enabled"]:
      pass
except KeyboardInterrupt:
  raise SystemExit
