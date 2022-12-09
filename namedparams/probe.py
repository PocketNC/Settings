import probe

def _probe_compensation_x(self):
  cal = probe.getInstance()
  return cal.getCompensationX()

def _probe_compensation_y(self):
  cal = probe.getInstance()
  return cal.getCompensationY()

def _probe_compensation_z(self):
  cal = probe.getInstance()
  return cal.getCompensationZ()

__all__ = [ k for k in globals().keys() if k.startswith("_probe") ]
