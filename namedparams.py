import metrology
import math
import probe

# TODO - Take into account units, leaving the metrology and probe modules units agnostic.
#      - The metrology and probe modules don't really need to know about units, but in G
#      - code you are dealing with either mm (G21) or inches (G20). We should probably 
#      - convert to machine units (whatever is set in [TRAJ]LINEAR_UNITS) from whatever
#      - the current mode is (mm when in G21 or inches when in G20). 
#      - We should do this conversion in oword.py and namedparams.py when point data
#      - is stored or requested by the user. This comment is duplicated in oword.py and namedparams.py.
#      - See SOFT-846.

manager = metrology.FeatureManager.getInstance()

def _f_points(self):
  feature = manager.getActiveFeature()
  print("in _f_points: %s" % (len(feature.points()),))
  return len(feature.points());

def _f_average_x(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  print("in _f_average_x: %s" % (avg[0],))

  return avg[0]

def _f_average_y(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  print("in _f_average_y: %s" % (avg[1],))

  return avg[1]

def _f_average_z(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  print("in _f_average_z: %s" % (avg[2],))

  return avg[2]

def _f_circle2d_center_x(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][0]

def _f_circle2d_center_y(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][1]

def _f_circle2d_radius(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[1]

def _f_circle2d_diameter(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return 2*circle2D[1]

def _f_line_direction_x(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return line[1][0]

def _f_line_direction_y(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return line[1][1]

def _f_line_angle_about_x(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan(line[1][1]/(-line[1][2]))

def _f_line_angle_about_y(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan((-line[1][2])/line[1][0])


def _f_line_angle_about_z(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan(line[1][1]/line[1][0])

def _probe_compensation_x(self):
  cal = probe.getInstance()
  return cal.getCompensationX()

def _probe_compensation_y(self):
  cal = probe.getInstance()
  return cal.getCompensationY()

def _probe_compensation_z(self):
  cal = probe.getInstance()
  return cal.getCompensationZ()
