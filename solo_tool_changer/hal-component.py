#!/usr/bin/python3

#********************************************************************
# Description:  solo_tool_changer
#               This file, 'solo_tool_changer.py', is a HAL component that 
#               controls the behavior of the tool changer drawer on the
#               Penta Solo machine.
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
from tool_info import is_over_tool_slot, get_tool_slot_position, get_tool_slot_num, TOOL_1_Z

h = hal.component("solo-tool-changer")

h.newpin("open-cmd", hal.HAL_BIT, hal.HAL_IN)
h.newpin("close-cmd", hal.HAL_BIT, hal.HAL_IN)
h.newpin("clamp-cmd", hal.HAL_BIT, hal.HAL_IN)
h.newpin("unclamp-cmd", hal.HAL_BIT, hal.HAL_IN)

# Performing a tool change while HIGH
h.newpin("tool-change-cmd", hal.HAL_BIT, hal.HAL_IN)

# Tool change numbers while performing tool change
h.newpin("old-tool", hal.HAL_S32, hal.HAL_IN)
h.newpin("new-tool", hal.HAL_S32, hal.HAL_IN)

# Spindle sensors for clamped with tool, clamped no tool or unclamped
h.newpin("clamped-no-tool", hal.HAL_BIT, hal.HAL_IN)
h.newpin("clamped-with-tool", hal.HAL_BIT, hal.HAL_IN)
h.newpin("unclamped", hal.HAL_BIT, hal.HAL_IN)

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

# spindle speeds for ensuring we don't unclamp a tool while spinning
# check measured speed as well as commanded speed for best reliability
h.newpin("spindle-speed-cmd", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("spindle-speed-measured", hal.HAL_FLOAT, hal.HAL_IN)

# outputs for controlling open/close solenoid
h.newpin("open-out", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("close-out", hal.HAL_BIT, hal.HAL_OUT)

# output for controlling tool clamp solenoid and reporting state
h.newpin("clamp-out", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("unclamp-out", hal.HAL_BIT, hal.HAL_OUT)

# outputs that reflect certain state machine states
h.newpin("ok-to-close", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("ok-to-open", hal.HAL_BIT, hal.HAL_OUT)

h.newpin("tool-change-complete", hal.HAL_BIT, hal.HAL_OUT)

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

pollTime = .1

h["open-cmd"] = False
h["close-cmd"] = False
h["clamp-cmd"] = False
h["unclamp-cmd"] = False
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
h["clamp-out"] =  False
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
    time.sleep(pollTime)
    
  while True:
    state.next()

    if state.is_clamp_requested:
      print("clamp was requested");
      # TODO - be smart about allowing clamping, perhaps ensure we're all the way down 
      # to the tool change position (but we likely need to allow the user to load a tool
      # manually, too)
      h["clamp-out"] = True
      h["unclamp-out"] = False
    elif state.is_unclamp_requested:
      print("unclamp was requested");
      # TODO - be smart about allowing unclamping, i.e. don't unclamp with spindle on.
      # Maybe only allow unclamping over a tool slot unless the user provides some
      # confirmation that the tool will be caught safely.
      h["clamp-out"] = False
      h["unclamp-out"] = True

    if (
      not h["x-homed"] or
      not h["y-homed"] or
      not h["z-homed"] or
      not h["b-homed"]
    ):
      h["z-min"] = Z_MIN-EPS
      h["x-min"] = X_MIN-EPS
      h["x-max"] = X_MAX+EPS
      h["y-min"] = Y_MIN+EPS
      h["y-max"] = Y_MAX-EPS
      h["b-min"] = B_MIN-EPS

# helps prevent accidental collisions when tool changer drawer is open
#    if (
#      not h["closed-sensor"] and 
#      h["x-homed"] and
#      h["y-homed"] and
#      h["z-homed"] and
#      h["b-homed"]
#    ):
#      # Drawer isn't closed and axes are homed
#
#      if h["x-position"] <= SAFE_X+EPS:
#        # Spindle not over tool changing drawer, full Z movement OK
#        h["z-min"] = Z_MIN-EPS
#
#        if h["z-position"] <= SAFE_Z-EPS:
#          # Z is lower than is safe when over the drawer, so limit X
#          h["x-max"] = SAFE_X+EPS
#        else:
#          # Z is at safe height to be over drawer, so allow full X movement
#          h["x-max"] = X_MAX
#      else:
#        # Spindle is over open tool changer drawer
#        if h["clamped-no-tool"] or h["unclamped"]:
#          if is_over_tool_slot(h["x-position"], h["y-position"]):
#            # Spindle is over a slot 
#
#            # TODO extra logic about which slots have tools loaded into them.
#            # If we know which slots have tools in them and which tool we have
#            # loaded, we can have extra safety precautions that prevent crashing
#            # into them.
#
#            if h["clamped-no-tool"]:
#              # Since we're not ejected, we would crash with a tool in the slot. We know we don't have a tool
#              # loaded, though, so we can safely go down 1 inch above the tool change Z position.
#              h["z-min"] = TOOL_1_Z+1-EPS
#            elif h["unclamped"]:
#              # we can safely go all the way down to tool change position
#              h["z-min"] = TOOL_1_Z-EPS
#
#            if h["z-position"] > TOOL_1_Z+1-EPS:
#              # No tool in spindle and we're at least 1 inch above tool loading position, so retracted far enough to move in x and y
#              h["x-min"] = X_MIN-EPS
#              h["x-max"] = X_MAX+EPS
#
#              h["y-min"] = Y_MIN+EPS
#              h["y-max"] = Y_MAX-EPS
#            else:
#              # Plunged far enough to disallow x,y movement
#              num = get_tool_slot_num(h["x-position"], h["y-position"], TOOL_1_Z)
#              slot = get_tool_slot_position(num)
#
#              # Don't allow x,y movement
#              h["x-min"] = slot[0]-EPS
#              h["x-max"] = slot[0]+EPS
#
#              h["y-min"] = slot[1]-EPS
#              h["y-max"] = slot[1]+EPS
#          else:
#            # Spindle is not over a tool slot
#
#            # Prevent Z plunge
#            h["z-min"] = TOOL_1_Z+1-EPS
#
#            # Allow full x,y movement
#            h["x-min"] = X_MIN-EPS
#            h["x-max"] = X_MAX+EPS
#
#            h["y-min"] = Y_MIN+EPS
#            h["y-max"] = Y_MAX-EPS
#        else:
#          # We have a tool in the spindle so we can't plunge unless over an empty tool slot
#          if is_over_tool_slot(h["x-position"], h["y-position"]):
#            # Spindle is over a slot 
#
#            # TODO extra logic about which slots have tools loaded into them.
#            # If we know which slots have tools in them and which tool we have
#            # loaded, we can have extra safety precautions that prevent crashing
#            # into them.
#
#            h["z-min"] = TOOL_1_Z-EPS
#
#            if h["z-position"] > SAFE_Z-EPS:
#              # Fully retracted, so allow x,y movement
#              h["x-min"] = X_MIN-EPS
#              h["x-max"] = X_MAX+EPS
#
#              h["y-min"] = Y_MIN+EPS
#              h["y-max"] = Y_MAX-EPS
#            else:
#              # Plunged far enough to disallow x,y movement
#              num = get_tool_slot_num(h["x-position"], h["y-position"], TOOL_1_Z)
#              slot = get_tool_slot_position(num)
#
#              # Don't allow x,y movement
#              h["x-min"] = slot[0]-EPS
#              h["x-max"] = slot[0]+EPS
#
#              h["y-min"] = slot[1]-EPS
#              h["y-max"] = slot[1]+EPS
#          else:
#            # Spindle is not over a tool slot
#
#            # Prevent Z plunge
#            h["z-min"] = SAFE_Z-EPS
#
#            # Allow full x,y movement
#            h["x-min"] = X_MIN-EPS
#            h["x-max"] = X_MAX+EPS
#
#            h["y-min"] = Y_MIN+EPS
#            h["y-max"] = Y_MAX-EPS

    state.update(pollTime)
    time.sleep(pollTime)

    while not h["enabled"]:
      time.sleep(pollTime)
except KeyboardInterrupt:
  raise SystemExit
