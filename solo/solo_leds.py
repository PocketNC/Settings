#!/usr/bin/python3

from PCA9634 import PCA9634
from i2c import busNum

import hal
import time

LED = PCA9634(0x73, busNum)
LED.soloConfig()
LED.blinkConfig(.5, 1)

def setEStopLED(estop):
  if estop:
    LED.LEDOn("RED_E-STOP")
    LED.LEDOff("GREEN_E-STOP")
  else:
    LED.LEDOff("RED_E-STOP")
    LED.LEDOn("GREEN_E-STOP")

def setCycleStartLED(paused, idle):
  if paused:
    LED.setPWM("CYCLE_START", 0xff)
    LED.LEDBlink("CYCLE_START")
  else:
    if not idle:
      LED.LEDOn("CYCLE_START")
    else:
      LED.setPWM("CYCLE_START", 0x1f)
      LED.LEDDim("CYCLE_START")

def setFeedHoldLED(idle):
  if not idle:
    LED.LEDOn("FEED_HOLD")
  else:
    LED.setPWM("FEED_HOLD", 0x1f)
    LED.LEDDim("FEED_HOLD")

def setPowerLED():
  LED.LEDOn("POWER_RED")
  LED.LEDOn("POWER_GREEN")
  LED.LEDOn("POWER_BLUE")

h = hal.component("solo-leds")

# pressure is a float from 0-1 that represents a parameter between minimum and maximum pressure
h.newpin("is-paused", hal.HAL_BIT, hal.HAL_IN)
h.newpin("is-idle", hal.HAL_BIT, hal.HAL_IN)
h.newpin("is-estopped", hal.HAL_BIT, hal.HAL_IN)

h.ready()

lastPaused = False
lastIdle = False
lastEStop = True

def updateLEDs(paused, idle, estop):
  setEStopLED(estop)
  setCycleStartLED(paused, idle)
  setFeedHoldLED(idle)
  setPowerLED()

updateLEDs(lastPaused, lastIdle, lastEStop)

update = False
try:
  while True:
    if h['is-paused'] != lastPaused:
      update = True
      lastPaused = h['is-paused']

    if h['is-idle'] != lastIdle:
      update = True
      lastIdle = h['is-idle']

    if h['is-estopped'] != lastEStop:
      update = True
      lastEStop = h['is-estopped']

    try:
      if update:
        updateLEDs(lastPaused, lastIdle, lastEStop)
        update = False
    except:
      pass

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

