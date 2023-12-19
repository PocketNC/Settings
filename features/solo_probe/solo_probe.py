#!/usr/bin/python3

import logging
from IrDA_Probe_I2C import IrDA_Probe_I2C
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

h.newpin("probe-on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("battery.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("battery.percentage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("battery.raw", hal.HAL_U32, hal.HAL_OUT)
h.newpin("beep.frequency", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("beep.duty_cycle", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("beep.on", hal.HAL_BIT, hal.HAL_IN)

h['beep.frequency'] = state['beep.frequency']
h['beep.duty_cycle'] = state['beep.duty_cycle']
h['beep.on'] = state['beep.on']
h["battery.voltage"] = -1
h["battery.percentage"] = -1
h['battery.raw'] = 0

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

  h["battery.voltage"] = voltage
  h["battery.percentage"] = percentage
  h["battery.raw"] = probe.BATTERY
except:
  logging.error("Error writing solo probe settings to I2C bus", exc_info=True)

h.ready()

lastProbeOn = False
lastBattery = time.time()
try:
  while True:
    try:
      if h["probe-on"] != lastProbeOn:
        if h["probe-on"]:
          # Probe was commanded to turn on
          probe.wake()
        else:
          # Probe was commanded to turn off
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

# if we haven't gotten a status from the battery, then check every 2 seconds
# otherwise, check only every minute
      if(
        (probe.BATTERY < 150 and time.time()-lastBattery > 2) or
        (time.time()-lastBattery > 60)
      ):
        probe.updateStatus()

        battery = probe.BATTERY & 0b00111111
        voltage = min(max(2.8 + battery / 45,3.3), 4.2)
        percentage = (voltage-3.3)/(4.2-3.3)*100

        h["battery.voltage"] = voltage
        h["battery.percentage"] = percentage
        h["battery.raw"] = probe.BATTERY

        lastBattery = time.time()
      lastProbeOn = h["probe-on"]
    except:
      pass

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

