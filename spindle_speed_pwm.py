#!/usr/bin/python3

import os
import sys
import datetime
import Adafruit_BBIO.PWM as PWM

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

pwmPin = "P8_13"

lastRPM = 0
lastSpindleOn = False
PWM.start(pwmPin, 50)

try:
  while True:
    if h['speed_in'] != lastRPM:
      currentRPM = h['speed_in']
      t = currentRPM/hiRPMParam
      currentFrequency = t*hiFrequencyParam
      if currentFrequency > 0:
        print "Setting frequency to %s" % currentFrequency
        PWM.set_frequency(pwmPin, currentFrequency)
      h['speed_measured'] = currentRPM
      lastRPM = currentRPM

    time.sleep(.1)


except KeyboardInterrupt:
  raise SystemExit

