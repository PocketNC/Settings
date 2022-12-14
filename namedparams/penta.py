import metrology
import logging

logger = logging.getLogger(__name__)

# TODO - Take into account units, leaving the metrology and probe modules units agnostic.
#      - The metrology and probe modules don't really need to know about units, but in G
#      - code you are dealing with either mm (G21) or inches (G20). We should probably 
#      - convert to machine units (whatever is set in [TRAJ]LINEAR_UNITS) from whatever
#      - the current mode is (mm when in G21 or inches when in G20). 
#      - We should do this conversion in oword.py and namedparams.py when point data
#      - is stored or requested by the user. This comment is duplicated in oword.py and namedparams.py.
#      - See SOFT-846.

manager = metrology.FeatureManager.getInstance()

def _penta_average_magnitude(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()

  points = feature.points()

  totalMag = 0
  numPoints = len(points)
  for p in points:
    totalMag += math.sqrt(p[0]*p[0]+p[1]*p[1]+p[2]*p[2])

  return totalMag/numPoints

def _penta_points(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  print("in _penta_points: %s" % (len(feature.points()),))
  return len(feature.points());

def _penta_average_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  avg = feature.average()

  print("in _penta_average_x: %s" % (avg[0],))

  return avg[0]

def _penta_average_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  avg = feature.average()

  print("in _penta_average_y: %s" % (avg[1],))

  return avg[1]

def _penta_average_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  avg = feature.average()

  print("in _penta_average_z: %s" % (avg[2],))

  return avg[2]

def _penta_circle2d_center_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][0]

def _penta_circle2d_center_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[0][1]

def _penta_circle2d_radius(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle2D = feature.circle2D()

  return circle2D[1]

def _penta_circle2d_diameter(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle2D = feature.circle2D()

  return 2*circle2D[1]

def _penta_circle_center_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[0][0]

def _penta_circle_center_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[0][1]

def _penta_circle_center_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[0][2]

def _penta_circle_radius(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[1]

def _penta_circle_diameter(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return 2*circle[1]

def _penta_circle_normal_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[2][0]

def _penta_circle_normal_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[2][1]

def _penta_circle_normal_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  circle = feature.circle()

  return circle[2][2]

def _penta_cylinder_point_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[0][0]

def _penta_cylinder_point_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[0][1]

def _penta_cylinder_point_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[0][2]

def _penta_cylinder_axis_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[1][0]

def _penta_cylinder_axis_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[1][1]

def _penta_cylinder_axis_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[1][2]

def _penta_cylinder_radius(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  cylinder = feature.cylinder()

  return cylinder[2]

def _penta_cylinder_diameter(self):
  return _penta_cylinder_radius(self)*2

def _penta_sphere_radius(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  sphere = feature.sphere()

  return sphere[0]

def _penta_sphere_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  sphere = feature.sphere()

  return sphere[1][0]

def _penta_sphere_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  sphere = feature.sphere()

  return sphere[1][1]

def _penta_sphere_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  sphere = feature.sphere()

  return sphere[1][2]

def _penta_sphere_diameter(self):
  return 2*_penta_sphere_radius(self)
  

def _penta_line_direction_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return line[1][0]

def _penta_line_direction_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return line[1][1]

def _penta_line_direction_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return line[1][2]

def _penta_line_angle_about_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return math.degrees(math.atan(line[1][1]/-line[1][2]))

def _penta_line_angle_about_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return math.degrees(math.atan(-line[1][2]/line[1][0]))


def _penta_line_angle_about_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  line = feature.line()

  return math.degrees(math.atan(line[1][1]/line[1][0]))

def _penta_plane_normal_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[1][0]

def _penta_plane_normal_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[1][1]

def _penta_plane_normal_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[1][2]

def _penta_plane_point_x(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[0][0]

def _penta_plane_point_y(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[0][1]

def _penta_plane_point_z(self):
  feature = manager.getActiveFeatureSet().getActiveFeature()
  plane = feature.plane()

  return plane[0][2]

__all__ = [ k for k in globals().keys() if k.startswith("_penta") ]
