#!/usr/bin/python
import hal, time
import logging
import logging.config
import uuid
import os
import struct

'''
have a file for storage
at startup, read value from file into tracking var
while we are running:
  with 1-sec sample frequency, track spindle on/off state
  when spindle is on, "accrete" time to tracking var
  when tracking var changes by >1 second since last file write, update file
'''

h = hal.component("timekeeper")
h.newpin("spindle-on", hal.HAL_BIT, hal.HAL_IN)
h.ready()

runTime = 0
with open("/home/pocketnc/time","wb+") as f:
  fc = f.read()
  runTime = int(fc,2) if len(fc) > 0 else 0
runTimeWritten = runTime

now = time.time()
last = now

try:
  while True:
    time.sleep(1)
    last = now
    now = time.time()

    if h['spindle-on']:
      runTime += (now - last)
      
    if(int(runTime) != runTimeWritten):
      try:
        with open("/home/pocketnc/time","wb") as f:
          runTimeWritten = int(runTime)
          f.write(bin(runTimeWritten))
      except IOError as e:
        print(e)

except KeyboardInterrupt:
  raise SystemExit
