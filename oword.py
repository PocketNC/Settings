import metrology
import probe
import math
import numpy
import kinematics
import ini
import os

from importlib import reload
reload(kinematics)

POCKETNC_VAR_DIRECTORY = os.environ.get("POCKETNC_VAR_DIRECTORY")
INI_PATH = os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini")
INI_CACHE = ini.read_ini_data(INI_PATH)

# TODO - Take into account units, leaving the metrology and probe modules units agnostic.
#      - The metrology and probe modules don't really need to know about units, but in G
#      - code you are dealing with either mm (G21) or inches (G20). We should probably 
#      - convert to machine units (whatever is set in [TRAJ]LINEAR_UNITS) from whatever
#      - the current mode is (mm when in G21 or inches when in G20). 
#      - We should do this conversion in oword.py and namedparams.py when point data
#      - is stored or requested by the user. This comment is duplicated in oword.py and namedparams.py.
#      - See SOFT-846.

def add_point(self, x=0, y=0, z=0):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.addPoint(x,y,z)

def clear_points(self):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.clearPoints()

def set_feature_transform_with_axis_angle(self, x, y, z, angle):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.setTransformWithAxisAngle([x,y,z], math.radians(angle))

# Used for allocating a new feature set to avoid stomping on data from
# other contexts. In a given routine that is using feature numbers,
# start the routine with "o<push_feature_set> call" and end it with
# "o<pop_feature_set> call" and the routine will have free reign to modify
# any feature without stomping on other's data
def push_feature_set(self):
  manager = metrology.FeatureManager.getInstance()
  manager.push()

def pop_feature_set(self):
  manager = metrology.FeatureManager.getInstance()
  manager.pop()

def set_active_feature(self, id):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  featureSet.setActiveFeatureID(id)

def set_probe_direction(self, dirx, diry, dirz):
  kinematicsStr = ini.get_parameter(INI_CACHE, "KINS", "KINEMATICS")["values"]["value"]

  tcpc_mode = self.params["_hal[motion.switchkins-type]"]
  if int(tcpc_mode) == 1:
    position = [
      self.params[5181],
      self.params[5182],
      self.params[5183],
      self.params[5184],
      self.params[5185],
      self.params[5186]
    ]
    (dirx, diry, dirz) = kinematics.transform_direction_local_to_global(kinematicsStr, position, dirx, diry, dirz)

  cal = probe.getInstance()
  cal.setProbeDirection(dirx, diry, dirz)

def disable_probe_calibration(self):
  cal = probe.getInstance()
  cal.disableCompensation()

def enable_probe_calibration(self):
  cal = probe.getInstance()
  cal.enableCompensation()

def intersect_lines(self, line1Id, line2Id, newId):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()

  line1Feature = featureSet.getFeature(line1Id)
  line2Feature = featureSet.getFeature(line2Id)
  newFeature = featureSet.getFeature(newId)

  newFeature.clearPoints()

  line1 = line1Feature.line()
  line2 = line2Feature.line()

  pts = metrology.intersectLines(line1, line2)

  for pt in pts:
    newFeature.addPoint(pt[0], pt[1], pt[2])

def project_points_onto_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  pointsFeature = featureSet.getFeature(pointsId)
  planeFeature = featureSet.getFeature(planeId)
  newFeature = featureSet.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)
    newFeature.addPoint(pointOnPlane[0], pointOnPlane[1], pointOnPlane[2])

def point_deviations_from_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  pointsFeature = featureSet.getFeature(pointsId)
  planeFeature = featureSet.getFeature(planeId)
  newFeature = featureSet.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)

    print("point: (%s, %s, %s)" % (p[0], p[1], p[2]))
    print("point on plane: (%s, %s, %s)" % (pointOnPlane[0], pointOnPlane[1], pointOnPlane[2]))

    dx = p[0]-pointOnPlane[0]
    dy = p[1]-pointOnPlane[1]
    dz = p[2]-pointOnPlane[2]
    print("mag: (%s)" % (math.sqrt(dx*dx+dy*dy+dz*dz),))

    newFeature.addPoint(dx,dy,dz)

def set_probe_calibration(self, actualDiameter, probeTipDiameter, rings, samplesPerRing, theta):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  cal = probe.getInstance()

  cal.setProbeCalibration(actualDiameter, probeTipDiameter, feature, rings, samplesPerRing, theta)

def save_probe_calibration(self):
  cal = probe.getInstance()
  cal.saveProbeCalibration()
