#!/usr/bin/python

import os
import sys

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
INI_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini")

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, get_parameter

import Adafruit_BBIO.GPIO as GPIO

try:
  from Adafruit_GPIO.I2C import Device
  i2c = Device(0x60, 2)
except:
  from Adafruit_I2C import Adafruit_I2C
  i2c = Adafruit_I2C(0x60)

import hal
import time

iniData = read_ini_data(INI_FILE)
spindleClockPinParam = get_parameter(iniData,"POCKETNC_PINS", "SPINDLE_CLOCK_PIN")

resetTime = time.time()
pulses = 0
def countPulses(x):
  global pulses
  pulses += 1

def resetPulses():
  global resetTime
  global pulses
  resetTime = time.time()
  pulses = 0

if spindleClockPinParam:
  GPIO.setup(spindleClockPinParam["values"]["value"], GPIO.IN)
  GPIO.add_event_detect(spindleClockPinParam["values"]["value"], GPIO.RISING, countPulses)

h = hal.component("spindle_voltage")
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

lastRPM = 0

try:
  while True:
    if h['speed_in'] != lastRPM:
      currentRPM = h['speed_in']
      t = (currentRPM-loRPM)/(hiRPM-loRPM)
      currentVoltage = max(min(loVoltage+(hiVoltage-loVoltage)*t, hiVoltage), loVoltage)
      currentDAC = int(currentVoltage/4.9*4095)

      i = min(max(currentDAC, 0), 4095)

      lo = i & 15 << 4
      hi = i >> 4

      combined = (lo << 8) | hi

      i2c.write16(64, combined)
      lastRPM = currentRPM
    time.sleep(.1)

    now = time.time()
    duration = now-resetTime
    if duration > 1:
        rpmMeasured = pulses/pulsesPerRevolution/duration*60
        resetPulses()
        h['speed_measured'] = rpmMeasured

except KeyboardInterrupt:
  raise SystemExit

