#!/usr/bin/python

import hal
import os
import datetime
import time

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
LAST_SPINDLE_OFF_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/last-spindle-off-time.txt")

print "Initializing hss_warmup!"
h = hal.component("hss_warmup")

h.newpin("spindle_on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("program_running", hal.HAL_BIT, hal.HAL_IN)
h.newpin("performing_warmup", hal.HAL_BIT, hal.HAL_IO)
h.newpin("abort", hal.HAL_BIT, hal.HAL_OUT)

h['abort'] = False

h.ready()

def checkSpindleActivity():
  try:
    f = open(LAST_SPINDLE_OFF_FILE, 'r');
    dateString = f.readline().strip()
    f.close();
  except:
    dateString = "2019-01-01T00:00:00.000000Z"

  now = datetime.datetime.utcnow()
  lastSpindleActivity = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%fZ")

  totalTime = (now-lastSpindleActivity).total_seconds()

# three days is 259200 seconds
#  return not h['performing_warmup'] and totalTime > 259200
  return not h['performing_warmup'] and totalTime > 10

lastSpindleOn = False

try:
  while True:
    if lastSpindleOn and not h['spindle_on'] and not h['performing_warmup']:
      print "recording last time spindle was turned off"
      f = open(LAST_SPINDLE_OFF_FILE, 'w');
      f.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ\n"))
      f.close()

    if h['spindle_on'] and not lastSpindleOn:
      abort = checkSpindleActivity()
      if abort:
        print "Aborting!"
      else:
        print "not aborting..."
      h['abort'] = abort

    if not h['program_running']:
      h['performing_warmup'] = False

    lastSpindleOn = h['spindle_on']
    time.sleep(.1)
except KeyboardInterrupt:
  raise SystemExit
