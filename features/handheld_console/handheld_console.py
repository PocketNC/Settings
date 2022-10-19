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

MAX_ENCODER_VALUE = 65535

ABS_HAL_MAX_VALUE = 2.0
ABS_DEADZONE      = 0.05
ABS_HAL_MID_VALUE = 1.0

halComponent = None
lcncCommand = None
lcncStatus = None
max_velocity = None
# Reference to the evdev Input Device for the HID Controller
hidConsole = None
last_jog_count = 0

lastDeviceCheck = datetime.datetime.utcnow()

# index 0 is left out 
# to indicate no selected axis
selectedAxisMap = {
  1: 'x',
  2: 'y',
  3: 'z',
  4: 'r1',
  5: 'r2',
}

jogScale = {
  0: 100,
  1: 10,
  2: 1
}

overrideEvents = {
    'ABS_X':lambda value: setPinValue('feed-override-value', value),
    'ABS_Y':lambda value: setPinValue('spindle-override-value', value),
    'ABS_Z':lambda value: setPinValue('velocity-override-value', value)
}

selectEvents = {
    'ABS_RX':lambda value: selectAxis(value),         # axis-select
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
  for joint in range(1, 6):
    axis = selectedAxisMap[joint]
    setPinValue(f'joint-select-{axis}', 0)
  # hand held console selected 0 == no axis  
  if (value != 0):
    # map the joint index to an axis
    # and set the pin to selected
    axis = selectedAxisMap[value]
    setPinValue(f'joint-select-{axis}', 1)

def selectJogIncrement(value):
  selectedScale = jogScale[value]

  linearJogIncrementBase = halComponent["linear-jog-incr-base"]
  rotaryJogIncrementBase = halComponent["rotary-jog-incr-base"]
  
  linearIncrement = linearJogIncrementBase / selectedScale
  rotaryIncrement = rotaryJogIncrementBase / selectedScale

  setPinValue('selected-linear-jog-incr', linearIncrement)
  setPinValue('selected-rotary-jog-incr', rotaryIncrement)

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

  halComponent.newpin('linear-jog-incr-base', hal.HAL_FLOAT, hal.HAL_IN)
  halComponent.newpin('rotary-jog-incr-base', hal.HAL_FLOAT, hal.HAL_IN)

  halComponent.newpin('selected-linear-jog-incr', hal.HAL_FLOAT, hal.HAL_OUT)
  halComponent.newpin('selected-rotary-jog-incr', hal.HAL_FLOAT, hal.HAL_OUT)
  halComponent.newpin('joint-selected-count', hal.HAL_S32, hal.HAL_OUT)
  halComponent.newpin('joint-select-x', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-y', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-z', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-r1', hal.HAL_BIT, hal.HAL_OUT)
  halComponent.newpin('joint-select-r2', hal.HAL_BIT, hal.HAL_OUT)


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

# If the hal component is loaded after the device is connected
# events are supressed unless a value on the console is changed
#
# manually pull all relevant axis values from the device
# and process their values
def syncInitialState():
  feedOverride = hidConsole.absinfo(ecodes.ABS_X)
  processOverrideEvent('ABS_X', feedOverride.value)

  spindleOverride = hidConsole.absinfo(ecodes.ABS_Y)
  processOverrideEvent('ABS_Y', spindleOverride.value)

  velocityOveride = hidConsole.absinfo(ecodes.ABS_Z)
  processOverrideEvent('ABS_Z', velocityOveride.value)

  selectedIncrement = hidConsole.absinfo(ecodes.ABS_RY)
  processSelectEvent('ABS_RY', selectedIncrement.value)

  selectedAxis = hidConsole.absinfo(ecodes.ABS_RX)
  processSelectEvent('ABS_RX', selectedAxis.value)

def processSelectEvent(selectEvendId, inputValue):
  updateFunction = selectEvents[selectEvendId]
  updateFunction(inputValue)

def processButtonEvent(buttonEventId, keyPressed):
  updateFunction = buttonEvents[buttonEventId]
  updateFunction(keyPressed)

def processOverrideEvent(overrideEvendId, inputValue):
  updateFunction = overrideEvents[overrideEvendId]

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

  if lcncStatus.task_mode != linuxcnc.MODE_MANUAL:
    lcncCommand.mode(linuxcnc.MODE_MANUAL)
    lcncCommand.wait_complete()
    lcncStatus.poll()

  if lcncStatus.motion_mode == linuxcnc.TRAJ_MODE_TELEOP:
    lcncCommand.teleop_enable(0)
    lcncCommand.wait_complete()

  delta = 0
  jogEvendId = ecodes.ABS[event.event.code]
  updateFunction = jogEvents[jogEvendId]
  inputValue = event.event.value

  currentCount = halComponent['joint-selected-count']

  delta = inputValue - last_jog_count

  if(delta >= MAX_ENCODER_VALUE):
      delta = -1
  elif(delta <= -(MAX_ENCODER_VALUE)):
      delta = 1

  last_jog_count = inputValue
  updateFunction(currentCount + delta)

  

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
              last_jog_count = 0
              # Toggle the NUM Lock LED to force a fresh report to be sent
              hidConsole.set_led(ecodes.LED_NUML, 0)
              time.sleep(LOOP_SLEEP)
              hidConsole.set_led(ecodes.LED_NUML, 1)
              time.sleep(LOOP_SLEEP)

              syncInitialState()

          lastDeviceCheck = datetime.datetime.now()

      else:
        try:
         
          for event in hidConsole.read_loop():
            inputEvent = evdev.categorize(event)

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in overrideEvents:
              overrideEvendId = ecodes.ABS[inputEvent.event.code]
              processOverrideEvent(overrideEvendId, inputEvent.event.value)

            if isinstance(inputEvent, evdev.events.KeyEvent):
              buttonEvendId = inputEvent.keycode

              if not isinstance(buttonEvendId, str):
                buttonEvendId = buttonEvendId[0] # sometimes multiple keycodes are returned for one button

              if buttonEvendId in buttonEvents:
                # keystate 1 == key down
                processButtonEvent(buttonEvendId, inputEvent.keystate == 1)  

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in selectEvents:
              selectEvendId = ecodes.ABS[inputEvent.event.code]
              processSelectEvent(selectEvendId, inputEvent.event.value)

            if isinstance(inputEvent, evdev.events.AbsEvent) and ecodes.ABS[inputEvent.event.code] in jogEvents:
              processJogEvent(inputEvent)

        except Exception as e:
          hidConsole = None
          last_jog_count = 0
          setPinValue("console-connected", 0)

      time.sleep(LOOP_SLEEP)
  except KeyboardInterrupt:
    raise SystemExit