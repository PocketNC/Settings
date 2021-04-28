#!/usr/bin/python
import hal, time
import logging
import logging.config
import uuid
import os
import struct
import sys
sys.path.append('/home/pocketnc/pocketnc/Settings')
import eeprom
import core

now = time.time()
last = now
lastWriteTime = now

h = hal.component("timekeeper")
h.newpin("spindle-on", hal.HAL_BIT, hal.HAL_IN)
h.ready()

# def isTicking():
#   return h['spindle-on']

# timekeeper = core.Timekeeper(isTicking=isTicking)
# timekeeper.run()

interface = core.EEPROMInterface()
runtime = interface.runtime

try:
  while True:

    time.sleep(1)
    last = now
    now = time.time()

    if h['spindle-on']:
      runtime += (now - last)
      
    if(int(runtime) != interface.runtime and (now - lastWriteTime) > core.WRITE_PERIOD):
      try:
        interface.write_next(runtime)
      except IOError as e:
        print(e)

except KeyboardInterrupt:
  raise SystemExit

