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

# set to true when an E Stop should occur
h.newpin("abort", hal.HAL_BIT, hal.HAL_OUT)

# set to true when aborted and reset by rockhopper after
# the error has been reported
h.newpin("aborted", hal.HAL_BIT, hal.HAL_OUT)

h['abort'] = False
h['aborted'] = False

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
abort = False

try:
  while True:
    if lastSpindleOn and not h['spindle_on'] and not h['performing_warmup'] and not abort:
      # if we turned the spindle off, record the current time
      # unless we cancelled the warm up sequence or someone tried to turn on the
      # spindle without warming up
      print "recording last time spindle was turned off"
      f = open(LAST_SPINDLE_OFF_FILE, 'w');
      f.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ\n"))
      f.close()

    if h['spindle_on'] and not lastSpindleOn:
      # if the spindle is being turned on, check whether we should abort
      abort = checkSpindleActivity()
      if abort:
        h['aborted'] = True
    else:
      abort = False

    h['abort'] = abort
    if not h['program_running']:
      # if the warm up sequence is canceled, then the performing_warmup
      # pin won't properly be turned off, so if a program isn't running
      # turn it off here
      h['performing_warmup'] = False

    lastSpindleOn = h['spindle_on']
    time.sleep(.1)
except KeyboardInterrupt:
  raise SystemExit
