import linuxcnc
import time

c = linuxcnc.command()
s = linuxcnc.stat()

def find_y_offset():
  c.mode(linuxcnc.MODE_MANUAL)
  c.wait_complete()
  c.teleop_enable(0)
  c.wait_complete()
  c.home(1)
  c.wait_complete()

  s.poll()
  while s.homed[1] != 1:
    time.sleep(.1)
    s.poll()

  c.mode(linuxcnc.MODE_MDI)
  c.wait_complete()
  c.mdi("o<find-y-offsets> call")
  c.wait_complete()

  s.poll()
  while s.interp_state != linuxcnc.INTERP_IDLE:
    time.sleep(.1)
    s.poll()

for i in range(100):
  find_y_offset()
