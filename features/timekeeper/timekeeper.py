#!/usr/bin/python3
import hal, time
import eeprom
import timekeeper_core

now = time.time()
last = now
lastWriteTime = now

h = hal.component("timekeeper")
h.newpin("spindle-on", hal.HAL_BIT, hal.HAL_IN)
h.newpin("spindle-seconds", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

# sig = hal.new_sig("spindle_seconds", hal.HAL_FLOAT)

try:
  interface = timekeeper_core.EEPROMInterface()
except IOError as e:
  print("Timekeeper: main EEPROM not detected, falling back to filesystem write.")
  interface = timekeeper_core.FilesystemInterface()

runtime = interface.runtime
h['spindle-seconds'] = runtime

try:
  while True:

    time.sleep(1)
    last = now
    now = time.time()

    if h['spindle-on']:
      runtime += (now - last)
      
    if(int(runtime) != interface.runtime and (now - lastWriteTime) > timekeeper_core.WRITE_PERIOD):
      try:
        interface.write_next(runtime)
        h['spindle-seconds'] = runtime
      except IOError as e:
        print(e)

except KeyboardInterrupt:
  raise SystemExit

