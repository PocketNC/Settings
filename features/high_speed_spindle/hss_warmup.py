#!/usr/bin/python

import hal
import os
import datetime
import time

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
LAST_SPINDLE_OFF_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/last-spindle-off-time.txt")

def readLastSpindleOffFromDisk():
  try:
    f = open(LAST_SPINDLE_OFF_FILE, 'r');
    dateString = f.readline().strip()
    f.close();
  except:
    dateString = "2019-01-01T00:00:00.000000Z"

  return dateString

def recordSpindleOff():
  global lastSpindleOff


  now = datetime.datetime.utcnow()
  lastSpindleOff = now

  f = open(LAST_SPINDLE_OFF_FILE, 'w');
  f.write(now.strftime("%Y-%m-%dT%H:%M:%S.%fZ\n"))
  f.close()

def checkFullWarmupNeeded():
  now = datetime.datetime.utcnow()

  totalTime = (now-lastSpindleOff).total_seconds()

# 7 days is 604800 seconds
  return totalTime > 604800

def checkWarmupNeeded():
  now = datetime.datetime.utcnow()

  totalTime = (now-lastSpindleOff).total_seconds()

# 12 hours is  43200 seconds
  return totalTime > 43200


lastSpindleOn = False
abort = False

print "Initializing hss_warmup!"
h = hal.component("hss_warmup")

lastSpindleOff = datetime.datetime.strptime(readLastSpindleOffFromDisk(), "%Y-%m-%dT%H:%M:%S.%fZ")

h.newpin("spindle_on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("program_running", hal.HAL_BIT, hal.HAL_IN)
h.newpin("program_paused", hal.HAL_BIT, hal.HAL_IN)
h.newpin("completed_warmup", hal.HAL_BIT, hal.HAL_IN)
h.newpin("performing_warmup", hal.HAL_BIT, hal.HAL_IO)
h.newpin("performing_full_warmup", hal.HAL_BIT, hal.HAL_IO)

# set to true when at least the short warm up is needed
h.newpin("warmup_needed", hal.HAL_BIT, hal.HAL_OUT)

# set to true when a full length warm up is needed
h.newpin("full_warmup_needed", hal.HAL_BIT, hal.HAL_OUT)

# set to true when an E Stop should occur
h.newpin("abort", hal.HAL_BIT, hal.HAL_OUT)

# set to true when aborted and reset by rockhopper after
# the error has been reported
h.newpin("aborted", hal.HAL_BIT, hal.HAL_OUT)

h['abort'] = False
h['aborted'] = False
h['warmup_needed'] = checkWarmupNeeded()
h['full_warmup_needed'] = checkFullWarmupNeeded()

h.ready()


try:
  while True:
    if ( h['completed_warmup'] or not h['warmup_needed'] ) and lastSpindleOn and not h['spindle_on']:
      # if we turned the spindle off, record the current time
      # unless we cancelled the warm up sequence or someone tried to turn on the
      # spindle without warming up
      recordSpindleOff();
      h['completed_warmup'] = False

    h['warmup_needed'] = checkWarmupNeeded()
    h['full_warmup_needed'] = checkFullWarmupNeeded()

    if h['spindle_on']:
      if not lastSpindleOn:
        # if the spindle is being turned on, check whether we should abort
        needs_warmup = h['warmup_needed']
        needs_full_warmup = h['full_warmup_needed']
        abort = needs_warmup and not h['performing_warmup']
        abort = abort or ( needs_full_warmup and not h['performing_full_warmup'] )
        if abort:
          h['aborted'] = True
      elif h['warmup_needed'] and not h['performing_warmup']:
        abort = True
        h['aborted'] = True
    else:
      abort = False

    h['abort'] = abort
    if not h['program_running'] and not h['program_paused']:
      # if the warm up sequence is canceled, then the performing_warmup
      # pin won't properly be turned off, so if a program isn't running (and it isn't paused)
      # turn it off here
      h['performing_warmup'] = False
      h['performing_full_warmup'] = False

    lastSpindleOn = h['spindle_on']
    time.sleep(.1)
except KeyboardInterrupt:
  raise SystemExit
