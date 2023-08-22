#!/usr/bin/python3

#********************************************************************
# Description:  solo_door
#               This file, 'solo_door/hal-component.py', is a HAL component that 
#               controls the behavior of the door on the Penta Solo machine.
#
# Author: John Allwine <john@pocketnc.com>
# License: GPL Version 2
#    
# Copyright (c) 2023 Pocket NC Company All rights reserved.
#
#*******************************************************************
import hal
import time
from state_machine import SoloDoorState
import penta_messages
import os

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

h = hal.component("solo-door")

h.newpin("open-cmd", hal.HAL_BIT, hal.HAL_IN)
h.newpin("close-cmd", hal.HAL_BIT, hal.HAL_IN)
h.newpin("reset-cmd", hal.HAL_BIT, hal.HAL_IN)

h.newpin("door-sensor-1", hal.HAL_BIT, hal.HAL_IN)
h.newpin("door-sensor-2", hal.HAL_BIT, hal.HAL_IN)

h.newpin("running", hal.HAL_BIT, hal.HAL_IN)
h.newpin("spindle-on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("cutting-fluid-is-on", hal.HAL_BIT, hal.HAL_IN)

# the actual max velocity of each joint
h.newpin("joint.0.max-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.1.max-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.2.max-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.3.max-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.4.max-velocity", hal.HAL_FLOAT, hal.HAL_IN)

# the max velocity of each joint when door is open
h.newpin("joint.0.open-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.1.open-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.2.open-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.3.open-velocity", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("joint.4.open-velocity", hal.HAL_FLOAT, hal.HAL_IN)

# outputs for controlling open/close solenoid
h.newpin("open-out", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("close-out", hal.HAL_BIT, hal.HAL_OUT)

# outputs for limiting machine movements/spindle
h.newpin("inhibit-spindle", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("joint.0.max-velocity-out", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("joint.1.max-velocity-out", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("joint.2.max-velocity-out", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("joint.3.max-velocity-out", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("joint.4.max-velocity-out", hal.HAL_FLOAT, hal.HAL_OUT)


# outputs for signaling a tool changer fault
h.newpin("fault", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("fault-reason", hal.HAL_S32, hal.HAL_OUT)

# debugging pin to show the internal state machine state
h.newpin("state", hal.HAL_S32, hal.HAL_OUT)
h.ready()

pollTime = .05

# default to not a fault condition, which will change 
# if improperly wired up or machine is in fault state
h["fault"] = False
h["fault-reason"] = False

state = SoloDoorState(h, messageClient)

try:
  while True:
    state.next()
    state.update(pollTime)
    time.sleep(pollTime)
except KeyboardInterrupt:
  raise SystemExit
