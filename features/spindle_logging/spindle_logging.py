#!/usr/bin/python3

import hal
import time
import logging
import logging.config
import uuid
import os

h = hal.component("spindle_logging")
h.newpin("speed_in", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("speed_measured", hal.HAL_FLOAT, hal.HAL_IN)
h.ready()

def ConfigureLogger(name, file):
  logger = logging.getLogger(name)
  formatter = logging.Formatter("%(message)s")
  fileHandler = logging.FileHandler(file, mode='a')
  fileHandler.setFormatter(formatter)
  streamFormatter = logging.Formatter("%(name)s %(message)s")
  streamHandler = logging.StreamHandler()
  streamHandler.setFormatter(streamFormatter)
  logger.setLevel(logging.INFO)
  logger.addHandler(fileHandler)
  logger.addHandler(streamHandler)

commandedName = "CommandedSpindle"
measuredName = "MeasuredSpindle"
uid = uuid.uuid4()

if not os.path.isdir("/home/pocketnc/spindle_logs"):
  os.mkdir("/home/pocketnc/spindle_logs")

ConfigureLogger(commandedName, "/home/pocketnc/spindle_logs/Commanded.csv")
ConfigureLogger(measuredName, "/home/pocketnc/spindle_logs/Measured.csv")

commandedLogger = logging.getLogger(commandedName)
measuredLogger  = logging.getLogger(measuredName)

lastMeasurementTime = time.time()
commandedLogger.info("%s\t0\tServer Started\t%s" % (lastMeasurementTime,uid))
measuredLogger.info("%s\t0\tServer Started\t%s" % (lastMeasurementTime,uid))

measurements = 0
lastRPM = 0

try:
  while True:
    if h['speed_in'] != lastRPM:
      currentRPM = h['speed_in']
      commandedLogger.info("%s\t%s" % (time.time(), lastRPM))
      commandedLogger.info("%s\t%s" % (time.time(), currentRPM))
      measurements = 10

      lastRPM = currentRPM

    time.sleep(.1)

    now = time.time()
    if now-lastMeasurementTime > 60:
      measurements += 1

    if now-lastMeasurementTime > 1:
      if measurements > 0:
        rpmMeasured = h['speed_measured']
        measuredLogger.info("%s\t%s" % (now, rpmMeasured))
        measurements -= 1
        lastMeasurementTime = now

except KeyboardInterrupt:
  raise SystemExit

