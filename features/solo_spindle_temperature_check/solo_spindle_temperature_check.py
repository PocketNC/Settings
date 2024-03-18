#!/usr/bin/python3

import hal
import time
import os
import penta_messages
import json

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

def send_temperature_fault():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle-over-temp", 
    "text": "The max spindle temperature was exceeded."
  }))

def send_sensor_error(e):
  if e == 1:
    messageClient.send(json.dumps({ 
      "type": "error", 
      "kind": "spindle-sensor", 
      "text": "Communication error with spindle cooler."
    }))
  elif e == 2:
    messageClient.send(json.dumps({ 
      "type": "error", 
      "kind": "spindle-sensor", 
      "text": "Invalid message data from spindle cooler."
    }))
  else:
    messageClient.send(json.dumps({ 
      "type": "error", 
      "kind": "spindle-sensor", 
      "text": "Unknown error from spindle cooler."
    }))

h = hal.component("spindle-check")

h.newpin("temperature-max-c", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("temperature-c", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("sensor-error", hal.HAL_S32, hal.HAL_IN)
h.newpin("spindle-cmd", hal.HAL_FLOAT, hal.HAL_IN);

h.newpin("ok-to-run", hal.HAL_BIT, hal.HAL_OUT);
h.newpin("abort", hal.HAL_BIT, hal.HAL_OUT);
h.newpin("spindle-stop", hal.HAL_BIT, hal.HAL_OUT);
h.newpin("inhibit-spindle", hal.HAL_BIT, hal.HAL_OUT);

h.ready()

h['temperature-max-c'] = 37.7777

# Keep track of how many polling cycles reported errors.
# We only check the temperature once every second, so if
# we haven't heard from the d5next within 10 seconds, treat
# it the same as if we exceeded the temperature limit.
sensorErrors = 0

sentError = False

try:
  while True:
    if h['sensor-error']:
      sensorErrors += 1
    else:
      sensorErrors = 0

    if h['temperature-c'] > h['temperature-max-c'] or sensorErrors > 10:
      if h['spindle-cmd'] > 0:
        h['abort'] = 1
        sentError = False
      else:
        h['abort'] = 0

      if not sentError:
        if h['temperature-c'] > h['temperature-max-c']:
          send_temperature_fault()
        else:
          send_sensor_error(h['sensor-error'])
        sentError = True
      h['ok-to-run'] = 0
      h['spindle-stop'] = 1
      h['inhibit-spindle'] = 1
    else:
      sentError = False
      h['abort'] = 0
      h['ok-to-run'] = 1
      h['spindle-stop'] = 0
      h['inhibit-spindle'] = 0

    time.sleep(1)
except KeyboardInterrupt:
  raise SystemExit
