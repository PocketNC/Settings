import linuxcnc
import time

c = linuxcnc.command()
s = linuxcnc.stat()

def probe_z_test():
  c.mode(linuxcnc.MODE_MANUAL)
  c.wait_complete()
  c.teleop_enable(0)
  c.wait_complete()
  c.home(2)
  c.wait_complete()

  s.poll()
  while s.homed[2] != 1:
    time.sleep(.1)
    s.poll()

  c.mode(linuxcnc.MODE_MDI)
  c.wait_complete()
  c.mdi("o<probe-z-test> call")
  c.wait_complete()

  s.poll()
  while s.interp_state != linuxcnc.INTERP_IDLE:
    time.sleep(.1)
    s.poll()

while True:
  probe_z_test()
