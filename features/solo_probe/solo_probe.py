#!/usr/bin/python3

import logging
from IrDA_Probe_I2C import IrDA_Probe_I2C, PROBE_STATE_NORMAL
from i2c import busNum
import hal
import time
import os
import json

address = 0x44

POCKETNC_VAR_DIRECTORY = os.environ['POCKETNC_VAR_DIRECTORY']
stateFileName = "solo-probe-settings.json"
stateFilePath = os.path.join(POCKETNC_VAR_DIRECTORY, stateFileName)
defaults = {
  "beep.frequency": 4186, # C8, last note on a piano, also about the loudest sound our piezo can make
  "beep.duty_cycle": .5,
  "beep.on": 1
}

if POCKETNC_VAR_DIRECTORY:
  try:
    with open(stateFilePath, "r") as file:
      state = json.loads(file.read())
  except:
    state = defaults

probe = IrDA_Probe_I2C(address, busNum)

h = hal.component("solo-probe")

# Probe on indicates that the probe is being used for a probing routine.
# We originally used it to wake and sleep the probe, but we've moved toward
# waking the probe up when it is about to be pulled from its slot and put
# back to sleep when it goes back into the drawer.
h.newpin("probe-on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("probe-awake", hal.HAL_BIT, hal.HAL_IO)
h.newpin("battery.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("battery.percentage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("battery.raw", hal.HAL_U32, hal.HAL_OUT)
h.newpin("battery.status", hal.HAL_S32, hal.HAL_OUT)
h.newpin("beep.frequency", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("beep.duty_cycle", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("beep.on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("tripped", hal.HAL_BIT, hal.HAL_IN)

h['beep.frequency'] = state['beep.frequency']
h['beep.duty_cycle'] = state['beep.duty_cycle']
h['beep.on'] = state['beep.on']
h["battery.voltage"] = -1
h["battery.percentage"] = -1
h['battery.raw'] = 0
h['battery.status'] = -1

try:
  probe.setBeep(state["beep.frequency"], state["beep.duty_cycle"])
  if state["beep.on"]:
    probe.beepON()
  else:
    probe.beepOFF()

  probe.updateStatus()

  battery = probe.BATTERY & 0b00111111
  voltage = min(max(2.8 + battery / 45,3.3), 4.2)
  percentage = (voltage-3.3)/(4.2-3.3)*100
  status = (probe.BATTERY & 0b11000000) >> 6

  h["battery.voltage"] = voltage
  h["battery.percentage"] = percentage
  h["battery.raw"] = probe.BATTERY
  h["battery.status"] = status
except:
  logging.error("Error writing solo probe settings to I2C bus", exc_info=True)

h.ready()

lastOnOrOff = time.time()
lastProbeOn = False
lastProbeAwake = False
lastTripped = False
lastBattery = time.time()
try:
  while True:
    try:
      if h["probe-on"] != lastProbeOn:
        lastOnOrOff = time.time()

        if h["probe-on"] and not h["probe-awake"]:
          h["probe-awake"] = True

      if time.time()-lastOnOrOff > 7200 and h["probe-awake"]:
        # Go to sleep if last probe on or off was more than 2 hours ago
        h["probe-awake"] = False

      if h["probe-awake"] != lastProbeAwake:
        if h["probe-awake"]:
          # Probe was commanded to turn on
          probe.wake()
        else:
          # Probe was commanded to turn off
          probe.sleep()

      if not h["tripped"] and lastTripped and not h["probe-awake"]:
        # If the probe was tripped while sleeping, it will wake up.
        # We need to put it back to sleep if the probe is off to save power.
        # When the probe is no longer tripped and the probe is supposed to be off,
        # go back to sleep.
        probe.sleep()

      if( h["beep.frequency"] != state["beep.frequency"] or 
          h["beep.duty_cycle"] != state["beep.duty_cycle"] or
          h["beep.on"] != state["beep.on"]):
        state["beep.frequency"] = h["beep.frequency"]
        state["beep.duty_cycle"] = h["beep.duty_cycle"]
        state["beep.on"] = h["beep.on"]
        try:
          probe.setBeep(state["beep.frequency"], state["beep.duty_cycle"])
          if state["beep.on"]:
            probe.beepON()
          else:
            probe.beepOFF()
        except:
          logging.error("Error writing solo probe settings to I2C bus", exc_info=True)

        try:
          with open(stateFilePath, "w") as file:
            file.write(json.dumps(state))
        except:
          logging.error("Error writing solo probe settings file", exc_info=True)

      if time.time()-lastBattery > 2:
        probe.readBattery()

        battery = probe.BATTERY & 0b00111111
        voltage = min(max(2.8 + battery / 45,3.3), 4.2)
        percentage = (voltage-3.3)/(4.2-3.3)*100
        status = (probe.BATTERY & 0b11000000) >> 6

        h["battery.voltage"] = voltage
        h["battery.percentage"] = percentage
        h["battery.raw"] = probe.BATTERY
        h["battery.status"] = status

        if probe.STATUS == PROBE_STATE_NORMAL and not h["probe-awake"] and not h["tripped"]:
          # The probe is reporting a normal state, but we should be off, so put the probe
          # back to sleep (this is likely due to the probe being tripped).
          probe.sleep()

        lastBattery = time.time()
      lastProbeAwake = h["probe-awake"]
      lastProbeOn = h["probe-on"]
      lastTripped = h["tripped"]
    except:
      pass

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

