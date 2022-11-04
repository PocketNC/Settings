#!/usr/bin/python3

import hal
import os
import datetime
import time
import json
import penta_messages

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
LAST_SPINDLE_OFF_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "last-spindle-off-time.txt")

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
lastPaused = False
abort = False

print("Initializing hss_warmup!")
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


h['abort'] = False
h['warmup_needed'] = checkWarmupNeeded()
h['full_warmup_needed'] = checkFullWarmupNeeded()

h.ready()

def send_full_warmup_needed_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_warmup", 
    "text": "You must run the full spindle warm up sequence (approx. 50 minutes) since it hasn't been turned on in over 1 week.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_short_warmup_needed_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_warmup", 
    "text": "You must run the short spindle warm up sequence (approx. 10 minutes) since it hasn't been turned on in over 12 hours.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))


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

    if h['spindle_on'] and not lastSpindleOn:
      # if the spindle is being turned on, check whether we should abort
      needs_warmup = h['warmup_needed']
      needs_full_warmup = h['full_warmup_needed']
      abort = needs_warmup and not h['performing_warmup']
      abort = abort or ( needs_full_warmup and not h['performing_full_warmup'] )
      if needs_full_warmup and not h['performing_full_warmup']:
        send_full_warmup_needed_message()
      elif needs_warmup and not h['performing_warmup']:
        send_short_warmup_needed_message()
    else:
      abort = False

    if (h['performing_warmup'] or h['performing_full_warmup']) and (h['program_paused'] and not lastPaused):
      abort = True

    h['abort'] = abort
    if not h['program_running'] and not h['program_paused']:
      # if the warm up sequence is terminated by a change in task_mode, 
      # the spindle doesn't stop automatically
      if h['spindle_on'] and (h['warmup_needed'] or h['performing_warmup']):
        h['abort'] = True
      # if the warm up sequence is canceled, then the performing_warmup
      # pin won't properly be turned off, so if a program isn't running (and it isn't paused)
      # turn it off here
      h['performing_warmup'] = False
      h['performing_full_warmup'] = False

    lastSpindleOn = h['spindle_on']
    lastPaused = h['program_paused']
    time.sleep(.1)
except KeyboardInterrupt:
  raise SystemExit
