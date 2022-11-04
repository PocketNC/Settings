#!/usr/bin/python3

import os
import sys
import datetime

POCKETNC_DIRECTORY = os.environ.get('POCKETNC_DIRECTORY')
INI_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini")

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, get_parameter
import hal
import time

iniData = read_ini_data(INI_FILE)

h = hal.component("spindle_speed")
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_measured", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

hiFrequencyParam = 40000.
hiRPMParam = 30000.

# 8.13
pwmPath = "/sys/class/pwm/pwmchip0/pwm-0:1"
periodPath = "%s/period" % pwmPath
dutyCyclePath = "%s/duty_cycle" % pwmPath
enablePath = "%s/enable" % pwmPath

with open(periodPath, "w") as periodF:
  periodF.write("10000")

with open(dutyCyclePath, "w") as dutyCycleF:
  dutyCycleF.write("10000")

with open(enablePath, "w") as enableF:
  enableF.write("1")

lastRPM = 0
lastSpindleOn = False

try:
  while True:
    if h['speed_in'] != lastRPM:
      currentRPM = h['speed_in']
      t = currentRPM/hiRPMParam
      currentFrequency = t*hiFrequencyParam
      if currentFrequency > 0:
        period = 1./currentFrequency*1e9
        with open(periodPath, "w") as periodF:
          periodF.write("%s" % int(period))

        with open(dutyCyclePath, "w") as dutyCycleF:
          dutyCycleF.write("%s" % int(period*.5))

      h['speed_measured'] = currentRPM
      lastRPM = currentRPM

    time.sleep(.1)


except KeyboardInterrupt:
  raise SystemExit

