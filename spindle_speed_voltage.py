#!/usr/bin/python3

import os
import sys
import datetime

POCKETNC_DIRECTORY = os.environ.get('POCKETNC_DIRECTORY')
POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')

INI_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini")

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, get_parameter
from i2c import bus

import hal
import time

iniData = read_ini_data(INI_FILE)

h = hal.component("spindle_speed")
h.newpin("spindle_clock_frequency", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_measured", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

loVoltageParam = get_parameter(iniData, "POCKETNC", "SPINDLE_LOW_VOLTAGE")
loRPMParam = get_parameter(iniData, "POCKETNC", "SPINDLE_LOW_RPM")

hiVoltageParam = get_parameter(iniData, "POCKETNC", "SPINDLE_HIGH_VOLTAGE")
hiRPMParam = get_parameter(iniData, "POCKETNC", "SPINDLE_HIGH_RPM")

pulsesPerRevolutionParam = get_parameter(iniData, "POCKETNC", "SPINDLE_PULSES_PER_REVOLUTION")
pulsesPerRevolution = float(pulsesPerRevolutionParam["values"]["value"]) if pulsesPerRevolutionParam else 4

loVoltage = float(loVoltageParam["values"]["value"]) if loVoltageParam else .24
loRPM = float(loRPMParam["values"]["value"]) if loRPMParam else 764.15

hiVoltage = float(hiVoltageParam["values"]["value"]) if hiVoltageParam else 2.49
hiRPM = float(hiRPMParam["values"]["value"]) if hiRPMParam else 10000.0

maxVoltage = 3

lastRPM = 0
lastSpindleOn = False

try:
  rpmMeasured = 0
  currentRPM = 0
  while True:
    if h['speed_in'] != lastRPM:
      currentRPM = h['speed_in']
      t = ((currentRPM)-loRPM)/(hiRPM-loRPM)
      currentVoltage = max(min(loVoltage+(hiVoltage-loVoltage)*t, maxVoltage), loVoltage)
      currentDAC = int(currentVoltage/4.9*4095)

      i = min(max(currentDAC, 0), 4095)

      lo = i & 15 << 4
      hi = i >> 4

      combined = (lo << 8) | hi

      try:
        bus.write_word_data(0x60, 64, combined)
      except:
        print("Failed to command spindle")
        
      lastRPM = currentRPM

    rpmMeasured = h["spindle_clock_frequency"]/pulsesPerRevolution*60
    if rpmMeasured <= 15:
      rpmMeasured = 0
    h["speed_measured"] = rpmMeasured

    time.sleep(.1)

except KeyboardInterrupt:
  raise SystemExit

