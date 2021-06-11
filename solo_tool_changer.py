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

h = hal.component("solo-tool-changer")

# set true to override outputs
h.newpin("override", hal.HAL_BIT, hal.HAL_IN)

# when override is true, outputs are set with these pins
h.newpin("override-open", hal.HAL_BIT, hal.HAL_IN)
h.newpin("override-close", hal.HAL_BIT, hal.HAL_IN)
h.newpin("override-inhibit-feed", hal.HAL_BIT, hal.HAL_IN)
h.newpin("override-inhibit-homing", hal.HAL_BIT, hal.HAL_IN)

# control for opening and closing tool changer
# when override is false

# used to open the tool changer via a program
h.newpin("open-cmd", hal.HAL_BIT, hal.HAL_IN)

# used to open the tool changer via MDI
h.newpin("manual-open-cmd", hal.HAL_BIT, hal.HAL_IN)

# inputs for making decisions about opening and closing the tool changer
# when override is false
h.newpin("x-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b-cmd-position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z-homed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("b-homed", hal.HAL_FLOAT, hal.HAL_IN)
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

h.newpin("intervention-required", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("intervention-reason", hal.HAL_HAL_S32, hal.HAL_OUT)
h.ready()

EPS = .000001
SAFE_Z = 0-EPS
SAFE_B = 0-EPS

timeSinceOpenOrCloseCmd = 0
pollTime = .2
timeAllowedToOpenOrClose = 4

h["open-cmd"] = False
h["manual-open-cmd"] = False

# default to input that would be considered a fault
h["closed-sensor"] = False
h["opened-sensor"] = False
h["b-position"] = -90
h["x-position"] = 4.5
h["y-position"] = 0
h["z-position"] = -6

# default to not driving the air solenoids and inhibit machine
# movement until we make a determination about what state the
# machine is in
h["open-out"] = False
h["close-out"] =  False
h["inhibit-feed"] = True
h["inhibit-homing"] = True

# default to not a fault condition, which will change 
# if improperly wired up or machine is in fault state
h["fault"] = False
h["fault-reason"] = False
h["user-intervention-required"] = False

FAULT_NOT_OPEN_OR_CLOSED = -1
FAULT_NOT_SAFE_TO_OPEN = -2
FAULT_NOT_SAFE_B_MOVE = -3
FAULT_NOT_HOMED_AND_NOT_CLOSED = -4

INTERVENTION_CLOSE_TOOL_CHANGER = -1

def safeToOpen():
  return (h["z-homed"] and
          h["b-homed"] and
          h["z-position"] >= SAFE_Z and
          h["b-position"] >= SAFE_B)

def checkInterventions():
  if( (not h["z-homed"] or
       not h["b-homed"]) and
      not h["closed-sensor"]):
    h["intervention-required"] = True
    h["intervention-reason"] = INTERVENTION_JOG_Z_AND_B_TO_SAFE_POSITION

  return False

def checkFaults():

  if( not h["opened-sensor"] and 
      not h["closed-sensor"] and 
      timeSinceOpenOrClosedCmd > timeToOpenOrClose
    ):
    h["fault"] = True
    h["fault-reason"] = FAULT_NOT_OPEN_OR_CLOSED

  if( not safeToOpen() and
      h["open-cmd"] and
      h["closed-sensor"] and
      h["homed"]):
    h["fault"] = True
    h["fault-reason"] = FAULT_NOT_SAFE_TO_OPEN

  if( h["b-cmd-position"] < SAFE_B and
      h["b-homed"] and
      not h["closed-sensor"]):
    h["fault"] = True
    h["fault-reason"] = FAULT_NOT_SAFE_B_MOVE

def 

try:
  while True:
    checkInterventions()
    checkFaults()
    driveOutputs()

    timeSinceOpenOrCloseCmd += pollTime
    time.sleep(pollTime)
except KeyboardInterrupt:
  raise SystemExit
