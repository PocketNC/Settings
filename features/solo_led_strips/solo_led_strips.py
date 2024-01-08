#!/usr/bin/python3

from SoloLEDStrip import SoloLEDStrip
from i2c import busNum

import hal
import time
import sys
import machinekit.hal
import os
import json

POCKETNC_VAR_DIRECTORY = os.environ['POCKETNC_VAR_DIRECTORY']

stateFileName = "solo-led-strips.json"
stateFilePath = os.path.join(POCKETNC_VAR_DIRECTORY, stateFileName)
defaults = {
  "override": 0,
  "override-status": 0
}

if POCKETNC_VAR_DIRECTORY:
  try:
    with open(stateFilePath, "r") as file:
      state = json.loads(file.read())
  except:
    state = defaults
    

statusSignalName = sys.argv[1]
halSignal = machinekit.hal.Signal(statusSignalName)

LEDs = SoloLEDStrip()

h = hal.component("solo-led-strips")

h.newpin("status", hal.HAL_S32, hal.HAL_IN)
h.newpin("reset", hal.HAL_BIT, hal.HAL_IN)
h.newpin("error", hal.HAL_BIT, hal.HAL_IN)
h.newpin("override", hal.HAL_BIT, hal.HAL_IN)
h.newpin("override-status", hal.HAL_S32, hal.HAL_IN)

lastStatus = 0
lastReset = 0
lastError = 0

h['override'] = state['override']
h['override-status'] = state['override-status']

lastOverride = 0
lastOverrideStatus = 0

h.ready()

def normal():
  LEDs.normal()

def error():
  LEDs.error()

def success():
  LEDs.success()

def party():
  LEDs.party()

def off():
  LEDs.off()

commands = [ normal, error, success, party, off ]

try:
  while True:
    if h['override-status'] != lastOverrideStatus or h['override'] != lastOverride:
      lastOverride = h['override']
      lastOverrideStatus = h['override-status']

      try:
        with open(stateFilePath, "w") as file:
          state['override'] = h['override']
          state['override-status'] = h['override-status']
          file.write(json.dumps(state))
      except:
        pass

      if h['override'] and h['override-status'] >= 0 and h['override-status'] < len(commands):
        commands[h['override-status']]()

      if not h['override'] and h['status'] >= 0 and h['status'] < len(commands):
        commands[h['status']]()

    if h['status'] != lastStatus:
      lastStatus = h['status']

      if not h['override'] and h['status'] >= 0 and h['status'] < len(commands):
        commands[h['status']]()

    if lastReset != h['reset']:
      lastReset = h['reset']

      if h['reset']:
        halSignal.set(0)

    if lastError != h['error']:
      lastError = h['error']

      if h['error']:
        halSignal.set(1)

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

