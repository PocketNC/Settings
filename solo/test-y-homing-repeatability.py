import linuxcnc
import time

c = linuxcnc.command()
s = linuxcnc.stat()

def probe_y_test():
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
  c.mdi("o<probe-y-test> call")
  c.wait_complete()

  s.poll()
  while s.interp_state != linuxcnc.INTERP_IDLE:
    time.sleep(.1)
    s.poll()

while True:
  probe_y_test()
