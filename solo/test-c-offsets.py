import linuxcnc
import time

c = linuxcnc.command()
s = linuxcnc.stat()

def find_c_offset():
  c.mode(linuxcnc.MODE_MANUAL)
  c.wait_complete()
  c.teleop_enable(0)
  c.wait_complete()
  c.home(4)
  c.wait_complete()

  s.poll()
  while s.homed[4] != 1:
    time.sleep(.1)
    s.poll()

  c.mode(linuxcnc.MODE_MDI)
  c.wait_complete()
  c.mdi("o<align-c-with-x> call")
  c.wait_complete()

  s.poll()
  while s.interp_state != linuxcnc.INTERP_IDLE:
    time.sleep(.1)
    s.poll()

for i in range(100):
  find_c_offset()
