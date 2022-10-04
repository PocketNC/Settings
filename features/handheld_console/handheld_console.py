#!/usr/bin/python3

#********************************************************************
# Description:  Handheld Console
#               This file, 'handheld_console.py', is a HAL component that 
#               interfaces with a Made With CNC Handheld Console via USB.
#
# Author: Chris Myers <chris.myers@madewithcnc.com>
# License: GPL Version 2
#    
# Copyright (c) 2022 Made With CNC All rights reserved.
#
#*******************************************************************

import hal
import linuxcnc
import evdev
from evdev import ecodes, _input, util
from select import select
from itertools import count, filterfalse as ifilterfalse
import time
import os
import sys
import datetime


POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
POCKETNC_INI_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini")

LOOP_SLEEP = 50 / 1000 # 50 milliseconds

ENCODER_COUNT_DIVIDER  = 4 
MAX_ENCODER_DELTA      = 65530
ENCODER_OVERFLOW_RESET = 2 ** 16 + ENCODER_COUNT_DIVIDER
JOG_DIVISOR            = 4

ABS_HAL_MAX_VALUE = 2.0
ABS_DEADZONE      = 0.05
ABS_HAL_MID_VALUE = 1.0

halComponent = None
lcncCommand = None
lcncStatus = None
max_velocity = None
# Reference to the evdev Input Device for the HID Controller
hidConsole = None
last_jog_count = None

lastDeviceCheck = datetime.datetime.utcnow()

# index 0 is left out 
# to indicate no selected axis
selectedAxisMap = {
  1: 'x',
  2: 'y',
  3: 'z',
  4: 'a',
  5: 'b',
}

imperialJogScale = {
  0: 0.0001,
  1: 0.001,
  2: 0.01
}

# TODO: Determine machine units
# ini does not appear to get updated when
# display units is changed on the client
# Look for units in the existing signals
metricJogScale = {
  1: 0.1,
  2: 0.01,
  3: 0.001
}

overrideEvents = {
    'ABS_X':lambda value: setPinValue('feed-override-value', value),
    'ABS_Y':lambda value: setPinValue('spindle-override-value', value),
    'ABS_Z':lambda value: setPinValue('velocity-override-value', value)
}

selectEvents = {
    'ABS_RX':lambda value: selectAxis(value), # axis-select
    'ABS_RY':lambda value: selectJogIncrement(value), # step-select
}

jogEvents = {
    'ABS_WHEEL':lambda value: setPinValue('joint-selected-count', value), # step encoder
}

buttonEvents = {
    'BTN_0':lambda value: setPinValue('feed-hold', value),   # feedhold
    'BTN_1':lambda value: setPinValue('cycle-start', value), # cycle start
    'BTN_2':lambda value: setPinValue('coolant', value),     # coolant
    'BTN_3':lambda value: setPinValue('program-stop', value) # stop
}

def selectAxis(value):
  # loop through all joints/axis and sent them
  # to unselected
  for joint in range(1, 5):
    axis = selectedAxisMap[joint]
    setPinValue(f'joint-select-{axis}', 0)
  # hand held console selected 0 == no axis  
  if (value != 0):
    # map the joint index to an axis
    # and set the pin to selected
    axis = selectedAxisMap[value]
    setPinValue(f'joint-select-{axis}', 1)

def selectJogIncrement(value):
  incr = imperialJogScale[value]
  setPinValue('selected-jog-incr', incr)

def setPinValue(pinName, value):
  halComponent[pinName] = value

def okToJog():
    lcncStatus.poll()
    return not lcncStatus.estop and lcncStatus.enabled and (lcncStatus.interp_state == linuxcnc.INTERP_IDLE)


def initHAL():
  halComponent.newpin('console-connected', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('feed-override-value', hal.HAL_S32, hal.HAL_OUT)
  halComponent.newpin('spindle-override-value', hal.HAL_S32, hal.HAL_OUT)
  halComponent.newpin('velocity-override-value', hal.HAL_S32, hal.HAL_OUT)

  halComponent.newpin('cycle-start', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('program-stop', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('feed-hold', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('coolant', hal.HAL_BIT, hal.HAL_OUT)

  #halComponent.newpin('is-idle', hal.HAL_BIT, hal.HAL_IN)
  halComponent.newpin('joint-mode', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('selected-jog-incr', hal.HAL_FLOAT, hal.HAL_OUT)
  halComponent.newpin('joint-selected-count', hal.HAL_S32, hal.HAL_OUT)
  halComponent.newpin('joint-select-x', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-y', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-z', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-a', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-b', hal.HAL_BIT, hal.HAL_OUT)


def hasAbsWheel(device):
    caps = device.capabilities()
    wheelAxis = next((axis for axis in caps.get(evdev.ecodes.EV_ABS, []) if axis[0] == evdev.ecodes.ABS_WHEEL), None)
    return not wheelAxis is None

def deviceSearch():
  # Search for something that has an ABS Axis of type Wheel defined
  hidDevice = next((dev for dev in [evdev.InputDevice(path) for path in evdev.list_devices()] 
    if ("Console" in dev.name) and hasAbsWheel(dev)), None)
  
  return hidDevice

def mapRange(value, input_min, input_max, output_min, output_max):
  return (value - input_min) * (output_max - output_min) / (input_max - input_min) + output_min;

def processSelectevent(event):
  selectEvendId = ecodes.ABS[event.event.code]
  updateFunction = selectEvents[selectEvendId]
  updateFunction(event.event.value)

def processButtonEvent(buttonEventId, keyPressed):
  updateFunction = buttonEvents[buttonEventId]
  updateFunction(keyPressed)

def processOverrideEvent(event):
  overrideEvendId = ecodes.ABS[event.event.code]
  updateFunction = overrideEvents[overrideEvendId]
  inputValue = event.event.value

  overrideHalMidValue = max_velocity / 2.0 if overrideEvendId == "ABS_Z" else ABS_HAL_MID_VALUE
  overrideHalMaxValue = max_velocity if overrideEvendId == "ABS_Z" else ABS_HAL_MAX_VALUE
  position = mapRange(inputValue, 0, 1024, 0, overrideHalMaxValue)
  position = round(position, 3)

  if (overrideHalMidValue - ABS_DEADZONE) <= position <= (overrideHalMidValue + ABS_DEADZONE):
      position = overrideHalMidValue

  # Apply Mid Range Dead Zone
  if (overrideHalMidValue - ABS_DEADZONE) <= position <= (overrideHalMidValue + ABS_DEADZONE):
    position = overrideHalMidValue
  # Apply Low Range Dead Zone
  if (ABS_DEADZONE > position):
    position = 0.0
  # Apply High Range Dead Zone    
  if (overrideHalMaxValue - ABS_DEADZONE < position):
    position = overrideHalMaxValue

  # We have to scale the value up to make it an INT
  # the HAL sets the Scale to .001
  position = position / 0.001

  updateFunction(position)


def processJogEvent(event):
  global last_jog_count

  if not okToJog():
    return

  delta = 0
  jogEvendId = ecodes.ABS[event.event.code]
  updateFunction = jogEvents[jogEvendId]
  inputValue = event.event.value

  setPinValue('joint-mode', 1)

  currentCount = halComponent['joint-selected-count']

  if (last_jog_count is None):
    last_jog_count = inputValue
  else:
    delta = inputValue - last_jog_count

    if(delta >= MAX_ENCODER_DELTA):
        delta = delta - ENCODER_OVERFLOW_RESET
    elif(delta <= -(MAX_ENCODER_DELTA)):
        delta = delta + ENCODER_OVERFLOW_RESET

    last_jog_count = inputValue
    delta = delta / JOG_DIVISOR
    updateFunction(currentCount + delta)

  setPinValue('joint-mode', 0)

if __name__ == "__main__":
  halComponent = hal.component("handheld_console")
  halComponent.setprefix("handheld_console")

  # Create HAL Pins
  initHAL()
  halComponent.ready()
  lcncCommand = linuxcnc.command()
  lcncStatus = linuxcnc.stat()

  # Read the configured MAX Velocity value to scale the velocity override
  # default to 1.732 if not found (1.732 is the default at the time of developing this module)
  inifile = linuxcnc.ini(POCKETNC_INI_FILE)
  max_velocity = float(inifile.find('TRAJ', 'MAX_LINEAR_VELOCITY') or 1.732)


  try:
    while True:
      if hidConsole is None:
        # only look for new USB devices every 5 seconds
        if (datetime.datetime.now() - lastDeviceCheck).total_seconds() > 5:
          hidConsole =  deviceSearch()
          if hidConsole is not None:
              setPinValue("console-connected", 1)
              last_jog_count = None
              # Force a fresh report to be sent
              hidConsole.set_led(ecodes.LED_NUML, 1)
              hidConsole.set_led(ecodes.LED_NUML, 0)

          lastDeviceCheck = datetime.datetime.now()

      else:
        try:
         
          for event in hidConsole.read_loop():
            inputEvent = evdev.categorize(event)

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in overrideEvents:
              processOverrideEvent(inputEvent)

            if isinstance(inputEvent, evdev.events.KeyEvent):
              buttonEvendId = inputEvent.keycode

              if not isinstance(buttonEvendId, str):
                buttonEvendId = buttonEvendId[0] # sometimes multiple keycodes are returned for one button

              if buttonEvendId in buttonEvents:
                # keystate 1 == key down
                processButtonEvent(buttonEvendId, inputEvent.keystate == 1)  

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in selectEvents:
              processSelectevent(inputEvent)

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in jogEvents:
              processJogEvent(inputEvent)

        except Exception as e:
          hidConsole = None
          last_jog_count = None
          setPinValue("console-connected", 0)

      time.sleep(LOOP_SLEEP)
  except KeyboardInterrupt:
    raise SystemExit