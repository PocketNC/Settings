import probe

def _probe_compensation_x(self):
  cal = probe.getInstance()
  return cal.getCompensation()[0]

def _probe_compensation_y(self):
  cal = probe.getInstance()
  return cal.getCompensation()[1]

def _probe_compensation_z(self):
  cal = probe.getInstance()
  return cal.getCompensation()[2]

__all__ = [ k for k in globals().keys() if k.startswith("_probe") ]
