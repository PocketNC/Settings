import metrology
import math

manager = metrology.FeatureManager.getInstance()

def _average_x(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  return avg[0]

def _average_y(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  return avg[1]

def _average_z(self):
  feature = manager.getActiveFeature()
  avg = feature.average()

  return avg[2]

def _circle2d_center_x(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][0]

def _circle2d_center_y(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][1]

def _circle2d_radius(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[1]

def _circle2d_diameter(self):
  feature = manager.getActiveFeature()
  circle2D = feature.circle2D()

  return 2*circle2D[1]

def _line_direction_x(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return line[1][0]

def _line_direction_y(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return line[1][1]

def _line_angle_about_x(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan(line[1][1]/(-line[1][2]))

def _line_angle_about_y(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan((-line[1][2])/line[1][0])


def _line_angle_about_z(self):
  feature = manager.getActiveFeature()
  line = feature.line()

  return math.atan(line[1][1]/line[1][0])
