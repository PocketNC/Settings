import metrology

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
  featureMap = manager.getActiveFeatureMap()
  feature = featureMap.getActiveFeature()
  feature.addPoint(x,y,z)

def clear_points(self):
  manager = metrology.FeatureManager.getInstance()
  featureMap = manager.getActiveFeatureMap()
  feature = featureMap.getActiveFeature()
  feature.clearPoints()

def set_feature_transform_with_axis_angle(self, x, y, z, angle):
  manager = metrology.FeatureManager.getInstance()
  featureMap = manager.getActiveFeatureMap()
  feature = featureMap.getActiveFeature()
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
  featureMap = manager.getActiveFeatureMap()
  featureMap.setActiveFeatureID(id)

def project_points_onto_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureMap = manager.getActiveFeatureMap()
  pointsFeature = featureMap.getFeature(pointsId)
  planeFeature = featureMap.getFeature(planeId)
  newFeature = featureMap.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)
    newFeature.addPoint(pointOnPlane[0], pointOnPlane[1], pointOnPlane[2])

def point_deviations_from_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureMap = manager.getActiveFeatureMap()
  pointsFeature = featureMap.getFeature(pointsId)
  planeFeature = featureMap.getFeature(planeId)
  newFeature = featureMap.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)

    logger.debug("point: (%s, %s, %s)" % (p[0], p[1], p[2]))
    logger.debug("point on plane: (%s, %s, %s)" % (pointOnPlane[0], pointOnPlane[1], pointOnPlane[2]))

    dx = p[0]-pointOnPlane[0]
    dy = p[1]-pointOnPlane[1]
    dz = p[2]-pointOnPlane[2]
    logger.debug("mag: (%s)" % (math.sqrt(dx*dx+dy*dy+dz*dz),))

    newFeature.addPoint(dx,dy,dz)

